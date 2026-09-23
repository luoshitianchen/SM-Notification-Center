"""新增业务表（通知渠道 / 通知记录 / 通知模板）

Revision ID: 0002_business_tables
Revises: 0001_initial
Create Date: 2026-09-23
"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# 本迁移由 autogenerate 生成，手动调整 revision 标识为 0002_business_tables
revision: str = '0002_business_tables'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 自动生成开始：创建通知业务表 ###
    # 通知渠道表：邮件 / 短信 /  webhook 等渠道配置
    op.create_table('notification_channels',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('channel_type', sa.String(length=16), nullable=False),
    sa.Column('config', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_channels_channel_type'), 'notification_channels', ['channel_type'], unique=False)
    op.create_index(op.f('ix_notification_channels_name'), 'notification_channels', ['name'], unique=True)
    op.create_index(op.f('ix_notification_channels_status'), 'notification_channels', ['status'], unique=False)
    # 通知记录表：每一条通知的发送状态与内容
    op.create_table('notification_records',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('channel_id', sa.String(length=64), nullable=False),
    sa.Column('template_code', sa.String(length=128), nullable=False),
    sa.Column('recipient', sa.String(length=256), nullable=False),
    sa.Column('subject', sa.String(length=256), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('error', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_records_channel_id'), 'notification_records', ['channel_id'], unique=False)
    op.create_index(op.f('ix_notification_records_recipient'), 'notification_records', ['recipient'], unique=False)
    op.create_index(op.f('ix_notification_records_status'), 'notification_records', ['status'], unique=False)
    op.create_index(op.f('ix_notification_records_template_code'), 'notification_records', ['template_code'], unique=False)
    # 通知模板表：按 code 管理标题与正文模板
    op.create_table('notification_templates',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('code', sa.String(length=128), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('channel_type', sa.String(length=16), nullable=False),
    sa.Column('title_template', sa.Text(), nullable=False),
    sa.Column('body_template', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='uq_template_code')
    )
    op.create_index(op.f('ix_notification_templates_channel_type'), 'notification_templates', ['channel_type'], unique=False)
    op.create_index(op.f('ix_notification_templates_code'), 'notification_templates', ['code'], unique=False)
    # ### 自动生成结束 ###


def downgrade() -> None:
    # ### 自动生成开始：回滚业务表 ###
    op.drop_index(op.f('ix_notification_templates_code'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_channel_type'), table_name='notification_templates')
    op.drop_table('notification_templates')
    op.drop_index(op.f('ix_notification_records_template_code'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_status'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_recipient'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_channel_id'), table_name='notification_records')
    op.drop_table('notification_records')
    op.drop_index(op.f('ix_notification_channels_status'), table_name='notification_channels')
    op.drop_index(op.f('ix_notification_channels_name'), table_name='notification_channels')
    op.drop_index(op.f('ix_notification_channels_channel_type'), table_name='notification_channels')
    op.drop_table('notification_channels')
    # ### 自动生成结束 ###
