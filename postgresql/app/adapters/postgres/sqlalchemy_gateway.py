from __future__ import annotations

import json

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.application.ports.database_gateway import DatabaseGateway


def build_async_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True, future=True)


class AsyncSqlAlchemyDatabaseGateway(DatabaseGateway):
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def ping(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def list_tables(self) -> list[str]:
        async with self.engine.connect() as conn:
            table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        return sorted(table_names)

    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        base_sql = """
            SELECT
                t.id,
                t.task_id,
                t.created_at,
                t.updated_at,
                t.result_path,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author,
                tr.file_name AS track_file_name,
                tr.file_path AS track_file_path,
                COALESCE(cc.comments_count, 0) AS comments_count,
                COALESCE(rc.reactions_like_count, 0) AS reactions_like_count,
                COALESCE(rc.reactions_fire_count, 0) AS reactions_fire_count,
                COALESCE(rc.reactions_wow_count, 0) AS reactions_wow_count
            FROM tablatures t
            JOIN visibilities v ON v.id = t.visibility_id
            JOIN task ta ON ta.id = t.task_id
            JOIN tracks tr ON tr.id = ta.track_id
            LEFT JOIN users u ON u.id = tr.user_id
            LEFT JOIN (
                SELECT
                    tablature_id,
                    COUNT(*)::int AS comments_count
                FROM tablature_comments
                GROUP BY tablature_id
            ) cc ON cc.tablature_id = t.id
            LEFT JOIN (
                SELECT
                    tablature_id,
                    COUNT(*) FILTER (WHERE lower(reaction_type) = 'like')::int AS reactions_like_count,
                    COUNT(*) FILTER (WHERE lower(reaction_type) = 'fire')::int AS reactions_fire_count,
                    COUNT(*) FILTER (WHERE lower(reaction_type) = 'wow')::int AS reactions_wow_count
                FROM tablature_reactions
                GROUP BY tablature_id
            ) rc ON rc.tablature_id = t.id
            WHERE lower(v.title) = 'public'
        """
        params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
        if query:
            base_sql += " AND (tr.file_name ILIKE :pattern OR CAST(t.id AS TEXT) ILIKE :pattern)"
            params["pattern"] = f"%{query.strip()}%"
        base_sql += " ORDER BY t.id DESC LIMIT :limit OFFSET :offset"

        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(base_sql), params)).mappings().all()
        return [dict(row) for row in rows]

    async def get_public_tablature(self, *, tablature_id: int) -> dict | None:
        sql = """
            SELECT
                t.id,
                t.task_id,
                t.created_at,
                t.updated_at,
                t.result_path,
                t.json_format,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author,
                tr.file_name AS track_file_name,
                tr.file_path AS track_file_path
            FROM tablatures t
            JOIN visibilities v ON v.id = t.visibility_id
            JOIN task ta ON ta.id = t.task_id
            JOIN tracks tr ON tr.id = ta.track_id
            LEFT JOIN users u ON u.id = tr.user_id
            WHERE lower(v.title) = 'public' AND t.id = :tablature_id
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), {"tablature_id": int(tablature_id)})).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def _public_tablature_exists(self, *, tablature_id: int) -> bool:
        sql = """
            SELECT 1
            FROM tablatures t
            JOIN visibilities v ON v.id = t.visibility_id
            WHERE t.id = :tablature_id AND lower(v.title) = 'public'
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            exists_row = await conn.execute(text(sql), {"tablature_id": int(tablature_id)})
            return exists_row.scalar_one_or_none() is not None

    async def list_public_tablature_comments(
        self,
        *,
        tablature_id: int,
        limit: int,
        offset: int,
    ) -> list[dict] | None:
        if not await self._public_tablature_exists(tablature_id=tablature_id):
            return None

        sql = """
            SELECT
                c.id,
                c.user_id,
                c.tablature_id,
                c.content,
                c.created_at,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM tablature_comments c
            JOIN users u ON u.id = c.user_id
            WHERE c.tablature_id = :tablature_id
            ORDER BY c.created_at DESC, c.id DESC
            LIMIT :limit OFFSET :offset
        """
        params = {
            "tablature_id": int(tablature_id),
            "limit": int(limit),
            "offset": int(offset),
        }
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
        return [dict(row) for row in rows]

    async def add_public_tablature_comment(
        self,
        *,
        tablature_id: int,
        user_id: int,
        content: str,
    ) -> dict | None:
        if not await self._public_tablature_exists(tablature_id=tablature_id):
            return None

        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Comment content is required")

        sql = """
            WITH inserted AS (
                INSERT INTO tablature_comments(user_id, tablature_id, content)
                VALUES (:user_id, :tablature_id, :content)
                RETURNING id, user_id, tablature_id, content, created_at
            )
            SELECT
                i.id,
                i.user_id,
                i.tablature_id,
                i.content,
                i.created_at,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM inserted i
            JOIN users u ON u.id = i.user_id
        """
        params = {
            "user_id": int(user_id),
            "tablature_id": int(tablature_id),
            "content": normalized_content,
        }
        async with self.engine.begin() as conn:
            row = (await conn.execute(text(sql), params)).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def get_public_tablature_reactions(
        self,
        *,
        tablature_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        if not await self._public_tablature_exists(tablature_id=tablature_id):
            return None

        counts_sql = """
            SELECT reaction_type, COUNT(*)::int AS cnt
            FROM tablature_reactions
            WHERE tablature_id = :tablature_id
            GROUP BY reaction_type
        """
        my_reaction_sql = """
            SELECT reaction_type
            FROM tablature_reactions
            WHERE tablature_id = :tablature_id AND user_id = :user_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """

        counts = {"like": 0, "fire": 0, "wow": 0}
        my_reaction: str | None = None
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(counts_sql), {"tablature_id": int(tablature_id)})).mappings().all()
            for row in rows:
                reaction_type = str(row["reaction_type"]).strip().lower()
                count = int(row["cnt"])
                if reaction_type in counts:
                    counts[reaction_type] = count

            if user_id is not None:
                my_reaction_value = await conn.execute(
                    text(my_reaction_sql),
                    {"tablature_id": int(tablature_id), "user_id": int(user_id)},
                )
                my_reaction = my_reaction_value.scalar_one_or_none()

        return {
            "tablature_id": int(tablature_id),
            "counts": counts,
            "total": int(sum(counts.values())),
            "my_reaction": my_reaction,
        }

    async def set_public_tablature_reaction(
        self,
        *,
        tablature_id: int,
        user_id: int,
        reaction_type: str,
    ) -> dict | None:
        if not await self._public_tablature_exists(tablature_id=tablature_id):
            return None

        normalized_reaction = reaction_type.strip().lower()
        if normalized_reaction not in {"like", "fire", "wow"}:
            raise ValueError("Unsupported reaction type")

        existing_sql = """
            SELECT reaction_type
            FROM tablature_reactions
            WHERE tablature_id = :tablature_id AND user_id = :user_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """
        delete_sql = """
            DELETE FROM tablature_reactions
            WHERE tablature_id = :tablature_id AND user_id = :user_id
        """
        insert_sql = """
            INSERT INTO tablature_reactions(tablature_id, user_id, reaction_type)
            VALUES (:tablature_id, :user_id, :reaction_type)
        """
        params = {"tablature_id": int(tablature_id), "user_id": int(user_id)}

        async with self.engine.begin() as conn:
            existing_row = await conn.execute(text(existing_sql), params)
            existing_reaction = existing_row.scalar_one_or_none()
            await conn.execute(text(delete_sql), params)

            # Toggle behavior: same reaction removes current reaction.
            if str(existing_reaction or "").strip().lower() != normalized_reaction:
                await conn.execute(
                    text(insert_sql),
                    {
                        "tablature_id": int(tablature_id),
                        "user_id": int(user_id),
                        "reaction_type": normalized_reaction,
                    },
                )

        return await self.get_public_tablature_reactions(
            tablature_id=int(tablature_id),
            user_id=int(user_id),
        )

    async def list_user_tablatures(self, *, user_id: int, query: str | None, limit: int, offset: int) -> list[dict]:
        base_sql = """
            SELECT
                t.id,
                t.task_id,
                t.created_at,
                t.updated_at,
                t.result_path,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author,
                tr.file_name AS track_file_name,
                tr.file_path AS track_file_path
            FROM tablatures t
            JOIN task ta ON ta.id = t.task_id
            JOIN tracks tr ON tr.id = ta.track_id
            LEFT JOIN users u ON u.id = tr.user_id
            WHERE tr.user_id = :user_id
        """
        params: dict[str, object] = {
            "user_id": int(user_id),
            "limit": int(limit),
            "offset": int(offset),
        }
        if query:
            base_sql += " AND (tr.file_name ILIKE :pattern OR CAST(t.id AS TEXT) ILIKE :pattern)"
            params["pattern"] = f"%{query.strip()}%"
        base_sql += " ORDER BY t.id DESC LIMIT :limit OFFSET :offset"

        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(base_sql), params)).mappings().all()
        return [dict(row) for row in rows]

    async def get_user_tablature(self, *, user_id: int, tablature_id: int) -> dict | None:
        sql = """
            SELECT
                t.id,
                t.task_id,
                t.created_at,
                t.updated_at,
                t.result_path,
                t.json_format,
                COALESCE(NULLIF(v.title, ''), 'private') AS visibility,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author,
                tr.file_name AS track_file_name,
                tr.file_path AS track_file_path
            FROM tablatures t
            JOIN task ta ON ta.id = t.task_id
            JOIN tracks tr ON tr.id = ta.track_id
            LEFT JOIN users u ON u.id = tr.user_id
            LEFT JOIN visibilities v ON v.id = t.visibility_id
            WHERE tr.user_id = :user_id AND t.id = :tablature_id
            LIMIT 1
        """
        params = {"user_id": int(user_id), "tablature_id": int(tablature_id)}
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), params)).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def _get_or_create_role_id(self, *, role_title: str) -> int:
        async with self.engine.begin() as conn:
            existing = await conn.execute(
                text("SELECT id FROM roles WHERE lower(role_title) = lower(:title) LIMIT 1"),
                {"title": role_title},
            )
            role_id = existing.scalar_one_or_none()
            if role_id is not None:
                return int(role_id)

            try:
                inserted = await conn.execute(
                    text("INSERT INTO roles(role_title) VALUES (:title) RETURNING id"),
                    {"title": role_title},
                )
                return int(inserted.scalar_one())
            except IntegrityError:
                race_row = await conn.execute(
                    text("SELECT id FROM roles WHERE lower(role_title) = lower(:title) LIMIT 1"),
                    {"title": role_title},
                )
                race_role_id = race_row.scalar_one_or_none()
                if race_role_id is None:
                    raise RuntimeError("Failed to resolve role id")
                return int(race_role_id)

    async def _get_or_create_visibility_id(self, *, visibility: str) -> int:
        title = visibility.strip().lower()
        if not title:
            raise ValueError("Visibility is required")

        async with self.engine.begin() as conn:
            existing = await conn.execute(
                text("SELECT id FROM visibilities WHERE lower(title) = :title LIMIT 1"),
                {"title": title},
            )
            visibility_id = existing.scalar_one_or_none()
            if visibility_id is not None:
                return int(visibility_id)

            try:
                inserted = await conn.execute(
                    text("INSERT INTO visibilities(title) VALUES (:title) RETURNING id"),
                    {"title": title},
                )
                return int(inserted.scalar_one())
            except IntegrityError:
                race_row = await conn.execute(
                    text("SELECT id FROM visibilities WHERE lower(title) = :title LIMIT 1"),
                    {"title": title},
                )
                race_visibility_id = race_row.scalar_one_or_none()
                if race_visibility_id is None:
                    raise RuntimeError("Failed to resolve visibility id")
                return int(race_visibility_id)

    async def update_user_tablature(
        self,
        *,
        user_id: int,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> dict | None:
        lookup_sql = """
            SELECT
                t.id AS tablature_id,
                t.task_id AS task_id,
                ta.track_id AS track_id
            FROM tablatures t
            JOIN task ta ON ta.id = t.task_id
            JOIN tracks tr ON tr.id = ta.track_id
            WHERE tr.user_id = :user_id AND t.id = :tablature_id
            LIMIT 1
        """
        params = {"user_id": int(user_id), "tablature_id": int(tablature_id)}
        async with self.engine.connect() as conn:
            ownership = (await conn.execute(text(lookup_sql), params)).mappings().first()
        if ownership is None:
            return None

        normalized_name: str | None = None
        if track_file_name is not None:
            normalized_name = track_file_name.strip()
            if normalized_name:
                duplicate_sql = """
                    SELECT t.id
                    FROM tablatures t
                    JOIN task ta ON ta.id = t.task_id
                    JOIN tracks tr ON tr.id = ta.track_id
                    WHERE tr.user_id = :user_id
                      AND lower(trim(tr.file_name)) = lower(:track_name)
                      AND t.id <> :tablature_id
                    LIMIT 1
                """
                async with self.engine.connect() as conn:
                    duplicate_row = (await conn.execute(
                        text(duplicate_sql),
                        {
                            "user_id": int(user_id),
                            "track_name": normalized_name,
                            "tablature_id": int(tablature_id),
                        },
                    )).scalar_one_or_none()
                if duplicate_row is not None:
                    raise ValueError("Tablature with this name already exists")

        visibility_id: int | None = None
        if visibility is not None:
            visibility_id = await self._get_or_create_visibility_id(visibility=visibility)

        async with self.engine.begin() as conn:
            if normalized_name:
                await conn.execute(
                    text("UPDATE tracks SET file_name = :name WHERE id = :track_id"),
                    {"name": normalized_name, "track_id": int(ownership["track_id"])},
                )

            tablature_updates: dict[str, object] = {}
            if visibility_id is not None:
                tablature_updates["visibility_id"] = int(visibility_id)
            if json_format is not None:
                tablature_updates["json_format"] = json_format

            if tablature_updates:
                set_clauses = []
                sql_params: dict[str, object] = {"tablature_id": int(ownership["tablature_id"])}
                for key, value in tablature_updates.items():
                    if key == "json_format":
                        set_clauses.append(f"{key} = CAST(:{key} AS json)")
                        sql_params[key] = json.dumps(value)
                    else:
                        set_clauses.append(f"{key} = :{key}")
                        sql_params[key] = value
                set_clauses.append("updated_at = now()")
                await conn.execute(
                    text(f"UPDATE tablatures SET {', '.join(set_clauses)} WHERE id = :tablature_id"),
                    sql_params,
                )

        return await self.get_user_tablature(user_id=int(user_id), tablature_id=int(tablature_id))

    async def get_user_by_email(self, *, email: str) -> dict | None:
        sql = """
            SELECT
                u.id,
                u.email,
                u.nickname,
                u.password_hash,
                r.role_title
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE lower(u.email) = lower(:email)
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), {"email": email})).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def get_user_by_id(self, *, user_id: int) -> dict | None:
        sql = """
            SELECT
                u.id,
                u.email,
                u.nickname,
                u.password_hash,
                r.role_title
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.id = :user_id
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), {"user_id": int(user_id)})).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def update_user_nickname(self, *, user_id: int, nickname: str) -> dict | None:
        sql = """
            UPDATE users
            SET nickname = :nickname
            WHERE id = :user_id
            RETURNING id, email, nickname
        """
        async with self.engine.begin() as conn:
            row = (await conn.execute(text(sql), {"user_id": int(user_id), "nickname": nickname})).mappings().first()
        if row is None:
            return None
        role_row = await self.get_user_by_id(user_id=int(row["id"]))
        if role_row is None:
            return None
        return role_row

    async def create_user(
        self,
        *,
        email: str,
        nickname: str,
        password_hash: str,
        role_title: str,
    ) -> dict:
        role_id = await self._get_or_create_role_id(role_title=role_title)
        sql = """
            INSERT INTO users(email, nickname, password_hash, role_id)
            VALUES (:email, :nickname, :password_hash, :role_id)
            RETURNING id, email, nickname
        """
        params = {
            "email": email,
            "nickname": nickname,
            "password_hash": password_hash,
            "role_id": role_id,
        }
        try:
            async with self.engine.begin() as conn:
                row = (await conn.execute(text(sql), params)).mappings().first()
        except IntegrityError as exc:
            raise ValueError("User with this email already exists") from exc

        if row is None:
            raise RuntimeError("Failed to create user")

        return {
            "id": int(row["id"]),
            "email": str(row["email"]),
            "nickname": str(row["nickname"]),
            "role_title": role_title,
        }
