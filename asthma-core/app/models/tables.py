"""
SQLAlchemy ORM 模型定义 V2
大创项目：基于入血预测的中医治疗儿童哮喘作用机制分析
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ==================== 实体表 ====================

class Herb(Base):
    """药材表 - V2 增强版，完全对齐前端展示"""
    __tablename__ = 'herb'

    id = Column(String(50), primary_key=True, comment='药材ID (ccTCM编号)')
    name = Column(String(100), nullable=False, comment='药材名称')
    pinyin = Column(String(100), comment='拼音')
    alias = Column(Text, comment='别名')
    latin_name = Column(String(200), comment='拉丁名/动物植物名')
    category = Column(String(50), comment='药物分类（如：补血药）')
    category_desc = Column(Text, comment='分类描述')
    functions = Column(Text, comment='功效')
    asthma_related = Column(Boolean, default=False, comment='是否哮喘相关')
    asthma_functions = Column(Text, comment='哮喘相关功效')
    nature = Column(String(20), comment='药性（寒/热/温/凉/平）')
    flavor = Column(String(50), comment='药味（辛/甘/酸/苦/咸）')
    meridians = Column(String(100), comment='归经')
    medicinal_part = Column(String(200), comment='药用部位')
    family = Column(String(100), comment='科属')
    dosage = Column(String(200), comment='用法用量')
    toxicity = Column(String(100), comment='毒性')
    contraindication = Column(Text, comment='禁忌')
    source = Column(Text, comment='来源')
    characteristics = Column(Text, comment='性状')
    identification = Column(Text, comment='鉴别')
    processing = Column(Text, comment='炮制')
    storage = Column(String(200), comment='贮藏')
    image = Column(String(500), comment='图片URL')
    compound_count = Column(Integer, comment='化合物数量')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    prescriptions = relationship(
        'Prescription',
        secondary='rel_prescription_herb',
        primaryjoin='Herb.name == RelPrescriptionHerb.herb_name',
        secondaryjoin='RelPrescriptionHerb.prescription_id == Prescription.id',
        back_populates='herbs'
    )
    compounds = relationship('Compound', secondary='rel_herb_compound', back_populates='herbs')

    __table_args__ = (
        Index('idx_herb_name', 'name'),
        Index('idx_herb_category', 'category'),
        Index('idx_herb_asthma_related', 'asthma_related'),
    )


class Compound(Base):
    """化合物表 - V2 增强版，含双模型概率+雷达评分"""
    __tablename__ = 'compound'

    id = Column(String(50), primary_key=True, comment='化合物ID (ccTCM编号)')
    name = Column(String(255), nullable=False, comment='化合物名称')
    smiles = Column(Text, comment='SMILES结构')
    smile_short = Column(String(100), comment='短SMILES（摘要用）')
    mw = Column(Float, comment='分子量')
    logp = Column(Float, comment='脂水分配系数')

    blood_entry_probability = Column(Float, comment='入血概率（前端展示用）')
    prob_cctcm = Column(Float, comment='ccTCM模型预测入血概率（高精度精英库）')
    prob_herb = Column(Float, comment='HERB模型预测入血概率（兜底全库）')

    asthma_related = Column(Boolean, default=False, comment='是否哮喘相关')

    radar_anti_inflammatory = Column(Float, comment='抗炎评分')
    radar_immune_regulation = Column(Float, comment='免疫调节评分')
    radar_airway_repair = Column(Float, comment='气道修复评分')

    target_count = Column(Integer, comment='靶点数量')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    herbs = relationship('Herb', secondary='rel_herb_compound', back_populates='compounds')
    targets = relationship('Target', secondary='rel_compound_target', back_populates='compounds')

    __table_args__ = (
        Index('idx_compound_name', 'name'),
        Index('idx_compound_blood_prob', 'blood_entry_probability'),
        Index('idx_compound_prob_cctcm', 'prob_cctcm'),
        Index('idx_compound_prob_herb', 'prob_herb'),
        Index('idx_compound_asthma_related', 'asthma_related'),
    )


class Target(Base):
    """靶点基因表 - V2 增强版"""
    __tablename__ = 'target'

    gene = Column(String(50), primary_key=True, comment='基因符号（如：TNF）')
    target_type = Column(Text, comment='靶点类型全称')
    species = Column(String(100), comment='物种')
    asthma_related = Column(Boolean, default=False, comment='是否哮喘相关')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    compounds = relationship('Compound', secondary='rel_compound_target', back_populates='targets')

    __table_args__ = (
        Index('idx_target_gene', 'gene'),
        Index('idx_target_asthma_related', 'asthma_related'),
    )


class Prescription(Base):
    """处方表"""
    __tablename__ = 'prescription'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='处方ID')
    name = Column(String(100), unique=True, nullable=False, comment='方剂名称')
    description = Column(Text, comment='方剂描述')
    core_effect = Column(String(200), comment='核心功效')
    indication_type = Column(String(200), comment='适用证型')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    herbs = relationship(
        'Herb',
        secondary='rel_prescription_herb',
        primaryjoin='Prescription.id == RelPrescriptionHerb.prescription_id',
        secondaryjoin='RelPrescriptionHerb.herb_name == Herb.name',
        back_populates='prescriptions'
    )

    __table_args__ = (
        Index('idx_prescription_name', 'name'),
    )


# ==================== 关联表（多对多） ====================

class RelHerbCompound(Base):
    """药材-化合物关联表"""
    __tablename__ = 'rel_herb_compound'

    id = Column(Integer, primary_key=True, autoincrement=True)
    herb_id = Column(String(50), ForeignKey('herb.id', ondelete='CASCADE'), comment='药材ID')
    compound_id = Column(String(50), ForeignKey('compound.id', ondelete='CASCADE'), comment='化合物ID')

    __table_args__ = (
        UniqueConstraint('herb_id', 'compound_id', name='uq_herb_compound'),
        Index('idx_rel_hc_herb', 'herb_id'),
        Index('idx_rel_hc_compound', 'compound_id'),
    )


class RelCompoundTarget(Base):
    """化合物-靶点关联表 - V2 增强版，带完整活性数据"""
    __tablename__ = 'rel_compound_target'

    id = Column(Integer, primary_key=True, autoincrement=True)
    compound_id = Column(String(50), ForeignKey('compound.id', ondelete='CASCADE'), comment='化合物ID')
    target_gene = Column(String(50), ForeignKey('target.gene', ondelete='CASCADE'), comment='靶点基因')

    activity_type = Column(String(100), comment='活性类型（如：Potency, Inhibition, Ki）')
    activity_value = Column(Float, comment='活性值')
    activity_unit = Column(String(20), comment='活性单位（如：nM, %）')

    reference = Column(String(500), comment='参考文献/数据集')
    network_centrality = Column(Float, comment='网络中心性')
    source_db = Column(String(50), comment='来源数据库（如：CTD, BindingDB）')

    __table_args__ = (
        Index('idx_rel_ct_compound', 'compound_id'),
        Index('idx_rel_ct_target', 'target_gene'),
    )


class RelPrescriptionHerb(Base):
    """处方-药材关联表"""
    __tablename__ = 'rel_prescription_herb'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, ForeignKey('prescription.id', ondelete='CASCADE'), comment='处方ID')
    herb_id = Column(String(50), comment='药材ID或药材名（兼容旧数据）')
    herb_name = Column(String(100), comment='药材名称')
    dosage = Column(String(50), comment='方剂级精确剂量，如 9g')

    __table_args__ = (
        UniqueConstraint('prescription_id', 'herb_id', name='uq_prescription_herb'),
        Index('idx_rel_ph_prescription', 'prescription_id'),
        Index('idx_rel_ph_herb', 'herb_id'),
    )


class User(Base):
    """用户表 - 登录注册"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希(bcrypt)')
    email = Column(String(100), comment='邮箱')
    role = Column(String(20), default='user', comment='角色(user/admin)')
    create_time = Column(DateTime, default=datetime.now, comment='注册时间')

    __table_args__ = (
        Index('idx_user_username', 'username'),
    )


__all__ = [
    "Base",
    "Prescription",
    "Herb",
    "Compound",
    "Target",
    "RelPrescriptionHerb",
    "RelHerbCompound",
    "RelCompoundTarget",
    "User",
]
