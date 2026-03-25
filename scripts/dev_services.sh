#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/dev_services.pid"

mkdir -p "$RUN_DIR" "$LOG_DIR"

print_usage() {
  cat <<'EOF'
Usage:
  ./scripts/dev_services.sh up       # start all services in background
  ./scripts/dev_services.sh down     # stop all services from pid file
  ./scripts/dev_services.sh down --keep-minio-server  # stop all except minio-server
  ./scripts/dev_services.sh restart  # restart all services
  ./scripts/dev_services.sh status   # show status
  ./scripts/dev_services.sh logs     # tail all logs
  ./scripts/dev_services.sh logs <service_name>  # tail one service log

Services started:
  postgresql-service  (8091)
  rabbitmq-service    (8090)
  minio-server        (9000, console 9001)
  minio-service       (8070)
  ml-api              (8000)
  ml-worker           (no http port)
  backend             (8080)
EOF
}

is_pid_running() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

is_port_listening() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

resolve_bin() {
  local local_path="$1"
  local fallback_name="$2"

  if [[ -x "$local_path" ]]; then
    printf '%s' "$local_path"
    return 0
  fi

  if command -v "$fallback_name" >/dev/null 2>&1; then
    command -v "$fallback_name"
    return 0
  fi

  return 1
}

start_service() {
  local name="$1"
  local workdir="$2"
  local cmd="$3"
  local logfile="$LOG_DIR/${name}.log"

  nohup bash -lc "cd '$workdir' && $cmd" >"$logfile" 2>&1 &
  local pid=$!
  echo "${name}|${pid}|${logfile}" >>"$PID_FILE"
  echo "started ${name} (pid=${pid})"
}

start_all() {
  if [[ -f "$PID_FILE" ]]; then
    local running_count=0
    while IFS='|' read -r _name pid _log; do
      [[ -z "${pid:-}" ]] && continue
      if is_pid_running "$pid"; then
        running_count=$((running_count + 1))
      fi
    done <"$PID_FILE"
    if [[ "$running_count" -gt 0 ]]; then
      echo "Services are already running. Use 'status' or 'restart'."
      exit 0
    fi
    rm -f "$PID_FILE"
  fi

  local postgre_uvicorn rabbitmq_uvicorn minio_uvicorn ml_uvicorn ml_python backend_uvicorn minio_bin
  postgre_uvicorn="$(resolve_bin "$ROOT_DIR/postgresql/.venv/bin/uvicorn" "uvicorn")" || {
    echo "uvicorn not found for postgresql-service"
    exit 1
  }
  rabbitmq_uvicorn="$(resolve_bin "$ROOT_DIR/rabbitmq/.venv/bin/uvicorn" "uvicorn")" || {
    echo "uvicorn not found for rabbitmq-service"
    exit 1
  }
  minio_uvicorn="$(resolve_bin "$ROOT_DIR/minio/.venv/bin/uvicorn" "uvicorn")" || {
    echo "uvicorn not found for minio-service"
    exit 1
  }
  ml_uvicorn="$(resolve_bin "$ROOT_DIR/ml-service/.venv/bin/uvicorn" "uvicorn")" || {
    echo "uvicorn not found for ml-api"
    exit 1
  }
  ml_python="$(resolve_bin "$ROOT_DIR/ml-service/.venv/bin/python" "python")" || {
    echo "python not found for ml-worker"
    exit 1
  }
  backend_uvicorn="$(resolve_bin "$ROOT_DIR/backend/.venv/bin/uvicorn" "uvicorn")" || {
    echo "uvicorn not found for backend"
    exit 1
  }
  minio_bin="$(resolve_bin "/opt/homebrew/bin/minio" "minio")" || {
    echo "minio binary not found for minio-server"
    exit 1
  }

  echo "Using executables:"
  echo "  postgresql-service: $postgre_uvicorn"
  echo "  rabbitmq-service:   $rabbitmq_uvicorn"
  echo "  minio-server:       $minio_bin"
  echo "  minio-service:      $minio_uvicorn"
  echo "  ml-api:             $ml_uvicorn"
  echo "  ml-worker:          $ml_python"
  echo "  backend:            $backend_uvicorn"

  : >"$PID_FILE"

  local minio_data_dir="$RUN_DIR/minio-data"
  mkdir -p "$minio_data_dir"

  start_service \
    "postgresql-service" \
    "$ROOT_DIR/postgresql" \
    "APP_PORT=8091 '$postgre_uvicorn' main:app --host 0.0.0.0 --port 8091 --reload"

  start_service \
    "rabbitmq-service" \
    "$ROOT_DIR/rabbitmq" \
    "'$rabbitmq_uvicorn' main:app --host 0.0.0.0 --port 8090 --reload"

  if is_port_listening "9000"; then
    echo "minio-server already listening on :9000, using existing instance."
  else
    start_service \
      "minio-server" \
      "$ROOT_DIR" \
      "MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin '$minio_bin' server '$minio_data_dir' --address :9000 --console-address :9001"
  fi

  start_service \
    "minio-service" \
    "$ROOT_DIR/minio" \
    "'$minio_uvicorn' main:app --host 0.0.0.0 --port 8070 --reload"

  start_service \
    "ml-api" \
    "$ROOT_DIR/ml-service" \
    "PYTHONPATH=src '$ml_uvicorn' ml_service.api.main:app --host 0.0.0.0 --port 8000 --reload"

  start_service \
    "ml-worker" \
    "$ROOT_DIR/ml-service" \
    "PYTHONPATH=src '$ml_python' -m ml_service.worker.main"

  start_service \
    "backend" \
    "$ROOT_DIR/backend" \
    "POSTGRES_SERVICE_URL=http://127.0.0.1:8091 ML_SERVICE_URL=http://127.0.0.1:8000 MINIO_SERVICE_URL=http://127.0.0.1:8070 '$backend_uvicorn' main:app --host 0.0.0.0 --port 8080 --reload"

  echo
  echo "All services started."
  echo "PID file: $PID_FILE"
  echo "Logs dir:  $LOG_DIR"
  echo "Check: ./scripts/dev_services.sh status"
}

stop_all() {
  local keep_minio_server="${1:-0}"
  local killed=0
  local force_killed=0
  local from_pid_file=0

  if [[ -f "$PID_FILE" ]]; then
    while IFS='|' read -r name pid _log; do
      [[ -z "${pid:-}" ]] && continue
      if [[ "$keep_minio_server" == "1" && "$name" == "minio-server" ]]; then
        echo "skip ${name} (keep running)"
        from_pid_file=$((from_pid_file + 1))
        continue
      fi
      if is_pid_running "$pid"; then
        kill "$pid" 2>/dev/null || true
        echo "stopped ${name} (pid=${pid})"
        killed=$((killed + 1))
      else
        echo "already stopped ${name} (pid=${pid})"
      fi
      from_pid_file=$((from_pid_file + 1))
    done <"$PID_FILE"
  else
    echo "No pid file found: $PID_FILE"
    echo "Trying best-effort stop by known ports and worker process..."
  fi

  sleep 1

  if [[ -f "$PID_FILE" ]]; then
    while IFS='|' read -r name pid _log; do
      [[ -z "${pid:-}" ]] && continue
      if [[ "$keep_minio_server" == "1" && "$name" == "minio-server" ]]; then
        continue
      fi
      if is_pid_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
        echo "force stopped ${name} (pid=${pid})"
        force_killed=$((force_killed + 1))
      fi
    done <"$PID_FILE"
  fi

  local known_ports=("8070" "8080" "8090" "8091" "8000")
  for port in "${known_ports[@]}"; do
    local pids
    pids="$(lsof -t -iTCP:${port} -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    [[ -z "$pids" ]] && continue
    while IFS= read -r pid; do
      [[ -z "${pid:-}" ]] && continue
      if is_pid_running "$pid"; then
        kill "$pid" 2>/dev/null || true
        echo "stopped process on port ${port} (pid=${pid})"
        killed=$((killed + 1))
      fi
    done <<<"$pids"
  done

  sleep 1
  for port in "${known_ports[@]}"; do
    local pids
    pids="$(lsof -t -iTCP:${port} -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    [[ -z "$pids" ]] && continue
    while IFS= read -r pid; do
      [[ -z "${pid:-}" ]] && continue
      if is_pid_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
        echo "force stopped process on port ${port} (pid=${pid})"
        force_killed=$((force_killed + 1))
      fi
    done <<<"$pids"
  done

  local worker_pids
  worker_pids="$(pgrep -f 'ml_service.worker.main' 2>/dev/null || true)"
  if [[ -n "$worker_pids" ]]; then
    while IFS= read -r pid; do
      [[ -z "${pid:-}" ]] && continue
      local cmdline
      cmdline="$(ps -p "$pid" -o command= 2>/dev/null || true)"
      if [[ "$cmdline" == *"$ROOT_DIR/ml-service"* ]]; then
        kill "$pid" 2>/dev/null || true
        echo "stopped ml-worker process (pid=${pid})"
        killed=$((killed + 1))
      fi
    done <<<"$worker_pids"
  fi

  rm -f "$PID_FILE"
  echo "Done. Services stopped: $killed (force stopped: $force_killed, pid-file entries: $from_pid_file)"
}

show_status() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "No running services (pid file not found)."
    exit 0
  fi

  while IFS='|' read -r name pid log; do
    [[ -z "${pid:-}" ]] && continue
    if is_pid_running "$pid"; then
      echo "[UP]   ${name} (pid=${pid}) log=${log}"
    else
      echo "[DOWN] ${name} (pid=${pid}) log=${log}"
    fi
  done <"$PID_FILE"
}

tail_logs() {
  local target="${1:-}"
  if [[ -n "$target" ]]; then
    local log="$LOG_DIR/${target}.log"
    if [[ ! -f "$log" ]]; then
      echo "Log not found: $log"
      exit 1
    fi
    tail -n 100 -f "$log"
    exit 0
  fi

  if ! ls "$LOG_DIR"/*.log >/dev/null 2>&1; then
    echo "No logs yet in $LOG_DIR"
    exit 0
  fi
  tail -n 50 -f "$LOG_DIR"/*.log
}

cmd="${1:-up}"
case "$cmd" in
  up)
    start_all
    ;;
  down)
    if [[ "${2:-}" == "--keep-minio-server" ]]; then
      stop_all 1
    else
      stop_all 0
    fi
    ;;
  restart)
    stop_all 0
    start_all
    ;;
  status)
    show_status
    ;;
  logs)
    tail_logs "${2:-}"
    ;;
  *)
    print_usage
    exit 1
    ;;
esac
