from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_scene: Mapped[str] = mapped_column(String(100), nullable=False, default="village")
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NPC(Base):
    __tablename__ = "npc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    current_scene: Mapped[str] = mapped_column(String(100), nullable=False)
    emotion_state: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class RelationshipState(Base):
    __tablename__ = "relationship_state"
    __table_args__ = (UniqueConstraint("player_id", "npc_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=False)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"), nullable=False)
    favorability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trust: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alertness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NPCMemory(Base):
    __tablename__ = "npc_memory"
    __table_args__ = (UniqueConstraint("npc_id", "content"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[str] = mapped_column(String(255), nullable=False)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    emotion_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    source_event: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Quest(Base):
    __tablename__ = "quest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quest_type: Mapped[str] = mapped_column(String(50), nullable=False)
    giver_npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"), nullable=False)
    target_scene: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_desc: Mapped[str] = mapped_column(Text, nullable=False)


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    __table_args__ = (UniqueConstraint("player_id", "quest_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=False)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quest.id"), nullable=False)
    current_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="locked")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DialogueLog(Base):
    __tablename__ = "dialogue_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=False)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"), nullable=False)
    player_input: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_result: Mapped[str] = mapped_column(String(100), nullable=False)
    chosen_action: Mapped[str] = mapped_column(String(100), nullable=False)
    npc_reply: Mapped[str] = mapped_column(Text, nullable=False)
    quest_update: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
