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

    async def list_public_courses(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        base_sql = """
            SELECT
                c.id,
                c.title,
                c.description,
                c.cover_image_path,
                c.created_at,
                c.updated_at,
                COALESCE(c.tags, ARRAY[]::text[]) AS tags,
                COALESCE(NULLIF(v.title, ''), 'private') AS visibility,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM course c
            JOIN visibilities v ON v.id = c.visibility_id
            JOIN users u ON u.id = c.user_id
            WHERE lower(v.title) = 'public'
        """
        params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
        if query:
            base_sql += """
                AND (
                    c.title ILIKE :pattern
                    OR COALESCE(c.description, '') ILIKE :pattern
                    OR COALESCE(NULLIF(u.nickname, ''), u.email, '') ILIKE :pattern
                    OR EXISTS (
                        SELECT 1
                        FROM unnest(COALESCE(c.tags, ARRAY[]::text[])) AS tag
                        WHERE tag ILIKE :pattern
                    )
                )
            """
            params["pattern"] = f"%{query.strip()}%"
        base_sql += " ORDER BY c.id DESC LIMIT :limit OFFSET :offset"

        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(base_sql), params)).mappings().all()

        items: list[dict] = []
        for row in rows:
            item = dict(row)
            tags = item.get("tags")
            if isinstance(tags, list):
                item["tags"] = [str(tag) for tag in tags]
            else:
                item["tags"] = []
            items.append(item)
        return items

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

    async def create_course(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> dict:
        visibility_id = await self._get_or_create_visibility_id(visibility=visibility or "public")
        insert_sql = """
            WITH inserted AS (
                INSERT INTO course(
                    user_id,
                    visibility_id,
                    title,
                    description,
                    cover_image_path,
                    tags
                )
                VALUES (
                    :user_id,
                    :visibility_id,
                    :title,
                    :description,
                    :cover_image_path,
                    :tags
                )
                RETURNING id, user_id, visibility_id, title, description, cover_image_path, tags, created_at, updated_at
            )
            SELECT
                i.id,
                i.title,
                i.description,
                i.cover_image_path,
                i.created_at,
                i.updated_at,
                COALESCE(i.tags, ARRAY[]::text[]) AS tags,
                COALESCE(NULLIF(v.title, ''), 'private') AS visibility,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM inserted i
            JOIN users u ON u.id = i.user_id
            JOIN visibilities v ON v.id = i.visibility_id
            LIMIT 1
        """
        params = {
            "user_id": int(user_id),
            "visibility_id": int(visibility_id),
            "title": title,
            "description": description,
            "cover_image_path": cover_image_path,
            "tags": list(tags or []),
        }
        async with self.engine.begin() as conn:
            row = (await conn.execute(text(insert_sql), params)).mappings().first()
        if row is None:
            raise RuntimeError("Failed to create course")
        item = dict(row)
        if isinstance(item.get("tags"), list):
            item["tags"] = [str(tag) for tag in item["tags"]]
        else:
            item["tags"] = []
        return item

    async def list_user_courses(self, *, user_id: int, query: str | None, limit: int, offset: int) -> list[dict]:
        base_sql = """
            SELECT
                c.id,
                c.title,
                c.description,
                c.cover_image_path,
                c.created_at,
                c.updated_at,
                COALESCE(c.tags, ARRAY[]::text[]) AS tags,
                COALESCE(NULLIF(v.title, ''), 'private') AS visibility,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM course c
            JOIN visibilities v ON v.id = c.visibility_id
            JOIN users u ON u.id = c.user_id
            WHERE c.user_id = :user_id
        """
        params: dict[str, object] = {
            "user_id": int(user_id),
            "limit": int(limit),
            "offset": int(offset),
        }
        if query:
            base_sql += """
                AND (
                    c.title ILIKE :pattern
                    OR COALESCE(c.description, '') ILIKE :pattern
                    OR CAST(c.id AS TEXT) ILIKE :pattern
                    OR EXISTS (
                        SELECT 1
                        FROM unnest(COALESCE(c.tags, ARRAY[]::text[])) AS tag
                        WHERE tag ILIKE :pattern
                    )
                )
            """
            params["pattern"] = f"%{query.strip()}%"
        base_sql += " ORDER BY c.id DESC LIMIT :limit OFFSET :offset"

        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(base_sql), params)).mappings().all()
        result: list[dict] = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("tags"), list):
                item["tags"] = [str(tag) for tag in item["tags"]]
            else:
                item["tags"] = []
            result.append(item)
        return result

    async def _get_user_course(self, *, user_id: int, course_id: int) -> dict | None:
        sql = """
            SELECT
                c.id,
                c.title,
                c.description,
                c.cover_image_path,
                c.created_at,
                c.updated_at,
                COALESCE(c.tags, ARRAY[]::text[]) AS tags,
                COALESCE(NULLIF(v.title, ''), 'private') AS visibility,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS author
            FROM course c
            JOIN visibilities v ON v.id = c.visibility_id
            JOIN users u ON u.id = c.user_id
            WHERE c.user_id = :user_id AND c.id = :course_id
            LIMIT 1
        """
        params = {"user_id": int(user_id), "course_id": int(course_id)}
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), params)).mappings().first()
        if row is None:
            return None
        item = dict(row)
        if isinstance(item.get("tags"), list):
            item["tags"] = [str(tag) for tag in item["tags"]]
        else:
            item["tags"] = []
        return item

    async def update_user_course(
        self,
        *,
        user_id: int,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> dict | None:
        existing = await self._get_user_course(user_id=user_id, course_id=course_id)
        if existing is None:
            return None

        visibility_id: int | None = None
        if visibility is not None:
            visibility_id = await self._get_or_create_visibility_id(visibility=visibility)

        updates: dict[str, object] = {}
        if title is not None:
            normalized_title = title.strip()
            if not normalized_title:
                raise ValueError("Course title is required")
            updates["title"] = normalized_title
        if description is not None:
            updates["description"] = description.strip() or None
        if visibility_id is not None:
            updates["visibility_id"] = int(visibility_id)
        if tags is not None:
            updates["tags"] = [str(tag) for tag in tags]
        if cover_image_path is not None:
            updates["cover_image_path"] = cover_image_path.strip() or None

        if not updates:
            return existing

        set_clauses = []
        params: dict[str, object] = {
            "course_id": int(course_id),
            "user_id": int(user_id),
        }
        for key, value in updates.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        set_clauses.append("updated_at = now()")

        sql = f"""
            UPDATE course
            SET {", ".join(set_clauses)}
            WHERE id = :course_id AND user_id = :user_id
        """
        async with self.engine.begin() as conn:
            await conn.execute(text(sql), params)

        return await self._get_user_course(user_id=user_id, course_id=course_id)

    async def delete_user_course(self, *, user_id: int, course_id: int) -> bool:
        sql = """
            DELETE FROM course
            WHERE id = :course_id AND user_id = :user_id
            RETURNING id
        """
        params = {"course_id": int(course_id), "user_id": int(user_id)}
        async with self.engine.begin() as conn:
            row = (await conn.execute(text(sql), params)).scalar_one_or_none()
        return row is not None

    async def _public_course_exists(self, *, course_id: int) -> bool:
        sql = """
            SELECT 1
            FROM course c
            JOIN visibilities v ON v.id = c.visibility_id
            WHERE c.id = :course_id AND lower(v.title) = 'public'
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = await conn.execute(text(sql), {"course_id": int(course_id)})
            return row.scalar_one_or_none() is not None

    async def _user_owns_course(self, *, user_id: int, course_id: int) -> bool:
        sql = """
            SELECT 1
            FROM course c
            WHERE c.id = :course_id AND c.user_id = :user_id
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = await conn.execute(
                text(sql),
                {"course_id": int(course_id), "user_id": int(user_id)},
            )
            return row.scalar_one_or_none() is not None

    async def _course_accessible_to_user(self, *, user_id: int, course_id: int) -> bool:
        sql = """
            SELECT 1
            FROM course c
            JOIN visibilities v ON v.id = c.visibility_id
            WHERE c.id = :course_id
              AND (c.user_id = :user_id OR lower(v.title) = 'public')
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = await conn.execute(
                text(sql),
                {"course_id": int(course_id), "user_id": int(user_id)},
            )
            return row.scalar_one_or_none() is not None

    async def _list_course_lessons(self, *, course_id: int) -> list[dict]:
        sql = """
            SELECT
                l.id,
                l.course_id,
                l.title,
                l.content,
                l.position,
                l.created_at,
                l.updated_at
            FROM course_lessons l
            WHERE l.course_id = :course_id
            ORDER BY l.position ASC, l.id ASC
        """
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(sql), {"course_id": int(course_id)})).mappings().all()
        return [dict(row) for row in rows]

    async def list_public_course_lessons(self, *, course_id: int) -> list[dict] | None:
        if not await self._public_course_exists(course_id=course_id):
            return None
        return await self._list_course_lessons(course_id=course_id)

    async def list_user_course_lessons(self, *, user_id: int, course_id: int) -> list[dict] | None:
        if not await self._user_owns_course(user_id=user_id, course_id=course_id):
            return None
        return await self._list_course_lessons(course_id=course_id)

    async def create_user_course_lesson(
        self,
        *,
        user_id: int,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> dict | None:
        if not await self._user_owns_course(user_id=user_id, course_id=course_id):
            return None

        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Lesson title is required")
        normalized_content = (content or "").strip()

        async with self.engine.begin() as conn:
            max_position_row = await conn.execute(
                text("SELECT COALESCE(MAX(position), 0) FROM course_lessons WHERE course_id = :course_id"),
                {"course_id": int(course_id)},
            )
            max_position = int(max_position_row.scalar_one() or 0)

            insert_position = max_position + 1
            if position is not None:
                insert_position = int(position)
                if insert_position < 1:
                    insert_position = 1
                if insert_position > max_position + 1:
                    insert_position = max_position + 1

            await conn.execute(
                text(
                    """
                    UPDATE course_lessons
                    SET position = position + 1
                    WHERE course_id = :course_id AND position >= :insert_position
                    """
                ),
                {"course_id": int(course_id), "insert_position": int(insert_position)},
            )

            inserted = await conn.execute(
                text(
                    """
                    INSERT INTO course_lessons(course_id, title, content, position)
                    VALUES (:course_id, :title, :content, :position)
                    RETURNING id, course_id, title, content, position, created_at, updated_at
                    """
                ),
                {
                    "course_id": int(course_id),
                    "title": normalized_title,
                    "content": normalized_content,
                    "position": int(insert_position),
                },
            )
            await conn.execute(
                text(
                    """
                    UPDATE course
                    SET updated_at = now()
                    WHERE id = :course_id
                    """
                ),
                {"course_id": int(course_id)},
            )
            row = inserted.mappings().first()
        if row is None:
            return None
        return dict(row)

    async def update_user_course_lesson(
        self,
        *,
        user_id: int,
        course_id: int,
        lesson_id: int,
        title: str | None = None,
        content: str | None = None,
        position: int | None = None,
    ) -> dict | None:
        if not await self._user_owns_course(user_id=user_id, course_id=course_id):
            return None

        lesson_sql = """
            SELECT id, course_id, title, content, position
            FROM course_lessons
            WHERE id = :lesson_id AND course_id = :course_id
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            existing = (await conn.execute(
                text(lesson_sql),
                {"lesson_id": int(lesson_id), "course_id": int(course_id)},
            )).mappings().first()
        if existing is None:
            return None

        new_title = str(existing["title"])
        if title is not None:
            new_title = title.strip()
            if not new_title:
                raise ValueError("Lesson title is required")

        new_content = str(existing.get("content") or "")
        if content is not None:
            new_content = content.strip()

        old_position = int(existing["position"])
        new_position = old_position

        async with self.engine.begin() as conn:
            max_position_row = await conn.execute(
                text("SELECT COALESCE(MAX(position), 0) FROM course_lessons WHERE course_id = :course_id"),
                {"course_id": int(course_id)},
            )
            max_position = int(max_position_row.scalar_one() or 0)

            if position is not None:
                new_position = int(position)
                if new_position < 1:
                    new_position = 1
                if new_position > max_position:
                    new_position = max_position

                if new_position < old_position:
                    await conn.execute(
                        text(
                            """
                            UPDATE course_lessons
                            SET position = position + 1
                            WHERE course_id = :course_id
                              AND position >= :new_position
                              AND position < :old_position
                            """
                        ),
                        {
                            "course_id": int(course_id),
                            "new_position": int(new_position),
                            "old_position": int(old_position),
                        },
                    )
                elif new_position > old_position:
                    await conn.execute(
                        text(
                            """
                            UPDATE course_lessons
                            SET position = position - 1
                            WHERE course_id = :course_id
                              AND position <= :new_position
                              AND position > :old_position
                            """
                        ),
                        {
                            "course_id": int(course_id),
                            "new_position": int(new_position),
                            "old_position": int(old_position),
                        },
                    )

            updated = await conn.execute(
                text(
                    """
                    UPDATE course_lessons
                    SET
                        title = :title,
                        content = :content,
                        position = :position,
                        updated_at = now()
                    WHERE id = :lesson_id AND course_id = :course_id
                    RETURNING id, course_id, title, content, position, created_at, updated_at
                    """
                ),
                {
                    "lesson_id": int(lesson_id),
                    "course_id": int(course_id),
                    "title": new_title,
                    "content": new_content,
                    "position": int(new_position),
                },
            )
            await conn.execute(
                text(
                    """
                    UPDATE course
                    SET updated_at = now()
                    WHERE id = :course_id
                    """
                ),
                {"course_id": int(course_id)},
            )
            row = updated.mappings().first()
        if row is None:
            return None
        return dict(row)

    async def delete_user_course_lesson(self, *, user_id: int, course_id: int, lesson_id: int) -> bool:
        if not await self._user_owns_course(user_id=user_id, course_id=course_id):
            return False

        async with self.engine.begin() as conn:
            deleted = await conn.execute(
                text(
                    """
                    DELETE FROM course_lessons
                    WHERE id = :lesson_id AND course_id = :course_id
                    RETURNING position
                    """
                ),
                {"lesson_id": int(lesson_id), "course_id": int(course_id)},
            )
            deleted_position = deleted.scalar_one_or_none()
            if deleted_position is None:
                return False

            await conn.execute(
                text(
                    """
                    UPDATE course_lessons
                    SET position = position - 1
                    WHERE course_id = :course_id AND position > :deleted_position
                    """
                ),
                {"course_id": int(course_id), "deleted_position": int(deleted_position)},
            )
        return True

    async def list_user_course_lesson_progress(self, *, user_id: int, course_id: int) -> list[dict] | None:
        if not await self._course_accessible_to_user(user_id=user_id, course_id=course_id):
            return None

        sql = """
            SELECT
                l.id AS lesson_id,
                COALESCE(p.is_completed, false) AS is_completed,
                p.completed_at,
                p.updated_at
            FROM course_lessons l
            LEFT JOIN user_lesson_progress p
              ON p.lesson_id = l.id
             AND p.user_id = :user_id
            WHERE l.course_id = :course_id
            ORDER BY l.position ASC, l.id ASC
        """
        params = {"user_id": int(user_id), "course_id": int(course_id)}
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
        return [dict(row) for row in rows]

    async def set_user_course_lesson_progress(
        self,
        *,
        user_id: int,
        course_id: int,
        lesson_id: int,
        completed: bool,
    ) -> dict | None:
        if not await self._course_accessible_to_user(user_id=user_id, course_id=course_id):
            return None

        lesson_exists_sql = """
            SELECT 1
            FROM course_lessons
            WHERE id = :lesson_id AND course_id = :course_id
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            exists = await conn.execute(
                text(lesson_exists_sql),
                {"lesson_id": int(lesson_id), "course_id": int(course_id)},
            )
            if exists.scalar_one_or_none() is None:
                return None

        completed_at_expr = "now()" if completed else "NULL"
        upsert_sql = f"""
            INSERT INTO user_lesson_progress(user_id, lesson_id, is_completed, completed_at, updated_at)
            VALUES (:user_id, :lesson_id, :is_completed, {completed_at_expr}, now())
            ON CONFLICT (user_id, lesson_id)
            DO UPDATE SET
                is_completed = EXCLUDED.is_completed,
                completed_at = {completed_at_expr},
                updated_at = now()
            RETURNING id, user_id, lesson_id, is_completed, completed_at, updated_at
        """
        params = {
            "user_id": int(user_id),
            "lesson_id": int(lesson_id),
            "is_completed": bool(completed),
        }
        async with self.engine.begin() as conn:
            row = (await conn.execute(text(upsert_sql), params)).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def track_user_course_visit(
        self,
        *,
        user_id: int,
        course_id: int,
    ) -> dict | None:
        if not await self._course_accessible_to_user(user_id=user_id, course_id=course_id):
            return None

        action_id = await self._get_or_create_action_id(action_title="course_first_visit")
        params = {
            "user_id": int(user_id),
            "course_id": int(course_id),
            "action_id": int(action_id),
        }

        async with self.engine.begin() as conn:
            existing_row = await conn.execute(
                text(
                    """
                    SELECT MIN(created_at) AS first_visit_at
                    FROM statistics
                    WHERE user_id = :user_id
                      AND course_id = :course_id
                      AND action_id = :action_id
                    """
                ),
                params,
            )
            first_visit_at = existing_row.scalar_one_or_none()
            if first_visit_at is not None:
                return {
                    "user_id": int(user_id),
                    "course_id": int(course_id),
                    "is_first_visit": False,
                    "first_visit_at": first_visit_at,
                }

            inserted_row = await conn.execute(
                text(
                    """
                    INSERT INTO statistics(user_id, action_id, course_id, created_at)
                    VALUES (:user_id, :action_id, :course_id, now())
                    RETURNING created_at
                    """
                ),
                params,
            )
            inserted_at = inserted_row.scalar_one_or_none()
            if inserted_at is None:
                return None

        return {
            "user_id": int(user_id),
            "course_id": int(course_id),
            "is_first_visit": True,
            "first_visit_at": inserted_at,
        }

    async def get_author_course_statistics(
        self,
        *,
        author_user_id: int,
        course_id: int,
    ) -> dict | None:
        if not await self._user_owns_course(user_id=author_user_id, course_id=course_id):
            return None

        course_title_sql = """
            SELECT title
            FROM course
            WHERE id = :course_id AND user_id = :author_user_id
            LIMIT 1
        """
        visitors_sql = """
            SELECT
                s.user_id,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS user_name,
                MIN(s.created_at) AS first_visit_at
            FROM statistics s
            JOIN actions a ON a.id = s.action_id
            JOIN users u ON u.id = s.user_id
            WHERE s.course_id = :course_id
              AND lower(a.title) = 'course_first_visit'
            GROUP BY s.user_id, COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown')
            ORDER BY first_visit_at ASC, s.user_id ASC
        """
        completions_sql = """
            SELECT
                p.user_id,
                COALESCE(NULLIF(u.nickname, ''), u.email, 'unknown') AS user_name,
                l.id AS lesson_id,
                l.title AS lesson_title,
                p.completed_at
            FROM user_lesson_progress p
            JOIN course_lessons l ON l.id = p.lesson_id
            JOIN users u ON u.id = p.user_id
            WHERE l.course_id = :course_id
              AND p.is_completed = true
              AND p.completed_at IS NOT NULL
            ORDER BY p.completed_at DESC, p.user_id ASC, l.position ASC, l.id ASC
        """
        params = {"course_id": int(course_id), "author_user_id": int(author_user_id)}
        async with self.engine.connect() as conn:
            course_title = (
                await conn.execute(
                    text(course_title_sql),
                    params,
                )
            ).scalar_one_or_none()
            if course_title is None:
                return None
            visitors_rows = (await conn.execute(text(visitors_sql), params)).mappings().all()
            completions_rows = (await conn.execute(text(completions_sql), params)).mappings().all()

        return {
            "course_id": int(course_id),
            "course_title": str(course_title),
            "visitors": [dict(row) for row in visitors_rows],
            "lesson_completions": [dict(row) for row in completions_rows],
        }

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

    async def _get_or_create_action_id(self, *, action_title: str) -> int:
        title = action_title.strip().lower()
        if not title:
            raise ValueError("Action title is required")

        async with self.engine.begin() as conn:
            existing = await conn.execute(
                text("SELECT id FROM actions WHERE lower(title) = :title LIMIT 1"),
                {"title": title},
            )
            action_id = existing.scalar_one_or_none()
            if action_id is not None:
                return int(action_id)

            try:
                inserted = await conn.execute(
                    text("INSERT INTO actions(title) VALUES (:title) RETURNING id"),
                    {"title": title},
                )
                return int(inserted.scalar_one())
            except IntegrityError:
                race_row = await conn.execute(
                    text("SELECT id FROM actions WHERE lower(title) = :title LIMIT 1"),
                    {"title": title},
                )
                race_action_id = race_row.scalar_one_or_none()
                if race_action_id is None:
                    raise RuntimeError("Failed to resolve action id")
                return int(race_action_id)

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

    async def get_latest_author_role_request(self, *, user_id: int) -> dict | None:
        sql = """
            SELECT
                r.id,
                r.user_id,
                r.message,
                r.status,
                r.admin_message,
                r.created_at,
                r.updated_at
            FROM author_role_requests r
            WHERE r.user_id = :user_id
            ORDER BY r.id DESC
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            row = (await conn.execute(text(sql), {"user_id": int(user_id)})).mappings().first()
        if row is None:
            return None
        return dict(row)

    async def create_author_role_request(self, *, user_id: int, message: str) -> dict:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Message is required")

        user = await self.get_user_by_id(user_id=int(user_id))
        if user is None:
            raise ValueError("User not found")
        if str(user.get("role_title") or "").strip().lower() == "author":
            raise ValueError("User already has author role")

        pending_sql = """
            SELECT id
            FROM author_role_requests
            WHERE user_id = :user_id AND lower(status) = 'pending'
            LIMIT 1
        """
        async with self.engine.connect() as conn:
            pending = await conn.execute(text(pending_sql), {"user_id": int(user_id)})
            if pending.scalar_one_or_none() is not None:
                raise ValueError("Pending author role request already exists")

        insert_sql = """
            INSERT INTO author_role_requests(user_id, message, status)
            VALUES (:user_id, :message, 'pending')
            RETURNING id, user_id, message, status, admin_message, created_at, updated_at
        """
        try:
            async with self.engine.begin() as conn:
                row = (await conn.execute(
                    text(insert_sql),
                    {"user_id": int(user_id), "message": normalized_message},
                )).mappings().first()
        except IntegrityError as exc:
            raise ValueError("Pending author role request already exists") from exc

        if row is None:
            raise RuntimeError("Failed to create author role request")
        return dict(row)

    async def list_author_role_requests(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        base_sql = """
            SELECT
                r.id,
                r.user_id,
                u.email AS user_email,
                u.nickname AS user_nickname,
                r.message,
                r.status,
                r.admin_message,
                r.created_at,
                r.updated_at
            FROM author_role_requests r
            JOIN users u ON u.id = r.user_id
            WHERE 1=1
        """
        params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
        if status is not None and status.strip():
            normalized_status = status.strip().lower()
            base_sql += " AND lower(r.status) = :status"
            params["status"] = normalized_status
        base_sql += " ORDER BY r.id DESC LIMIT :limit OFFSET :offset"

        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(base_sql), params)).mappings().all()
        return [dict(row) for row in rows]

    async def update_author_role_request_status(
        self,
        *,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> dict | None:
        normalized_status = status.strip().lower()
        if normalized_status not in {"pending", "approved", "rejected"}:
            raise ValueError("Invalid status")
        normalized_admin_message: str | None = None
        if admin_message is not None:
            candidate = admin_message.strip()
            if candidate:
                normalized_admin_message = candidate
        if normalized_status == "rejected" and not normalized_admin_message:
            raise ValueError("Admin message is required for rejected status")

        author_role_id: int | None = None
        if normalized_status == "approved":
            author_role_id = await self._get_or_create_role_id(role_title="author")

        async with self.engine.begin() as conn:
            existing = (await conn.execute(
                text(
                    """
                    SELECT id, user_id, message, status, admin_message, created_at, updated_at
                    FROM author_role_requests
                    WHERE id = :request_id
                    LIMIT 1
                    """
                ),
                {"request_id": int(request_id)},
            )).mappings().first()
            if existing is None:
                return None

            updated = (await conn.execute(
                text(
                    """
                    UPDATE author_role_requests
                    SET
                        status = :status,
                        admin_message = :admin_message,
                        updated_at = now()
                    WHERE id = :request_id
                    RETURNING id, user_id, message, status, admin_message, created_at, updated_at
                    """
                ),
                {
                    "status": normalized_status,
                    "request_id": int(request_id),
                    "admin_message": normalized_admin_message if normalized_status == "rejected" else None,
                },
            )).mappings().first()
            if updated is None:
                return None

            if normalized_status == "approved" and author_role_id is not None:
                await conn.execute(
                    text(
                        """
                        UPDATE users
                        SET role_id = :author_role_id
                        WHERE id = :user_id
                        """
                    ),
                    {
                        "author_role_id": int(author_role_id),
                        "user_id": int(updated["user_id"]),
                    },
                )
                # Keep requests table clean: once approved and role granted, request is no longer relevant.
                await conn.execute(
                    text("DELETE FROM author_role_requests WHERE id = :request_id"),
                    {"request_id": int(request_id)},
                )

            user_row = (await conn.execute(
                text("SELECT email, nickname FROM users WHERE id = :user_id LIMIT 1"),
                {"user_id": int(updated["user_id"])},
            )).mappings().first()

        payload = dict(updated)
        if user_row is not None:
            payload["user_email"] = str(user_row.get("email") or "")
            payload["user_nickname"] = str(user_row.get("nickname") or "")
        else:
            payload["user_email"] = ""
            payload["user_nickname"] = ""
        return payload
