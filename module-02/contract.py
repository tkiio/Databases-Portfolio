"""Application and database contracts for the repaired maintenance schema."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.schema import CreateTable


class MachineContract(BaseModel):
    machine_id: int = Field(ge=1)
    serial_no: str = Field(min_length=3)
    site: str
    installed: date

    @field_validator("serial_no")
    @classmethod
    def serial_has_prefix(cls, value: str) -> str:
        if not value.startswith("SN-"):
            raise ValueError("serial numbers must start with 'SN-'")
        return value


class PartContract(BaseModel):
    part_no: str = Field(min_length=1)
    description: str = Field(min_length=1)
    unit_price: Decimal = Field(ge=0)


class TechnicianContract(BaseModel):
    technician_id: int = Field(ge=1)
    name: str = Field(min_length=1)


class MaintenanceJobContract(BaseModel):
    job_id: int = Field(ge=1)
    machine_id: int = Field(ge=1)
    technician_id: int = Field(ge=1)
    done_on: date
    part_nos: list[str] = Field(default_factory=list)


metadata = MetaData()

machine_t = Table(
    "machine",
    metadata,
    Column("machine_id", Integer, primary_key=True),
    Column("serial_no", String, nullable=False),
    Column("site", String, nullable=False),
    Column("installed", Date, nullable=False),
    UniqueConstraint("serial_no", name="uq_machine_serial"),
)

technician_t = Table(
    "technician",
    metadata,
    Column("technician_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

part_t = Table(
    "part",
    metadata,
    Column("part_no", String, primary_key=True),
    Column("description", String, nullable=False),
    Column("unit_price", Numeric(9, 2), nullable=False),
)

maint_job_t = Table(
    "maint_job",
    metadata,
    Column("job_id", Integer, primary_key=True),
    Column("machine_id", Integer, ForeignKey("machine.machine_id"), nullable=False),
    Column(
        "technician_id",
        Integer,
        ForeignKey("technician.technician_id"),
        nullable=False,
    ),
    Column("done_on", Date, nullable=False),
)

job_part_t = Table(
    "job_part",
    metadata,
    Column("job_id", Integer, ForeignKey("maint_job.job_id"), primary_key=True),
    Column("part_no", String, ForeignKey("part.part_no"), primary_key=True),
)


if __name__ == "__main__":
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    for table in (machine_t, technician_t, part_t, maint_job_t, job_part_t):
        print(f"-- {table.name}")
        print(f"{CreateTable(table).compile(engine)};\n")
