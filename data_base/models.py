from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from data_base.database import METADATA

t_camera = Table(
    "tcamera",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FName", String(255), index=True),
    Column("FDateCreate", DateTime),
    Column("FRTSP", String(255)),
    Column("FDesc", String(255)),
    Column("FDateLastModify", DateTime),
    Column("isPlateRecEnable", Integer)
)

t_camera_groups = Table(
    "tcameragroups",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FCameraID", Integer, ForeignKey("tcamera.FID")),
    Column("FAsteriskCallerID", Integer, ForeignKey("tasteriskcaller.FID"))
)

t_asterisk_caller = Table(
    "tasteriskcaller",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FName", String(255))
)

# EVENT

t_event = Table(
    "tevent",
    METADATA,
    Column("FID", Integer, primary_key=True, index=True),
    Column("FEventTypeID", Integer, index=True),
    Column("FDateEvent", DateTime),
    Column("FDateRegistration", DateTime),
    Column("FOwnerName", String(25)),
    Column("FEventMessage", String(255)),
    Column("FEventDescription", String(512)),
    Column("FProcessed", Integer)
)
