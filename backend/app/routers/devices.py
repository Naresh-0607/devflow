from fastapi import APIRouter, HTTPException, Response, status

import uuid

from sqlalchemy import select

from app.deps import CurrentDevice, CurrentUser, DbSession
from app.models import Device
from app.schemas import DeviceCreate, DeviceCreated, DeviceOut
from app.security import generate_api_key

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/me", response_model=DeviceOut)
async def current_device(device: CurrentDevice) -> DeviceOut:
    """Used by the local agent to verify its API key."""
    return DeviceOut.model_validate(device)


@router.get("", response_model=list[DeviceOut])
async def list_devices(user: CurrentUser, db: DbSession) -> list[DeviceOut]:
    devices = (
        await db.execute(
            select(Device).where(Device.user_id == user.id).order_by(Device.created_at.desc())
        )
    ).scalars()
    return [DeviceOut.model_validate(device) for device in devices]


@router.post("", response_model=DeviceCreated, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate, user: CurrentUser, db: DbSession
) -> DeviceCreated:
    plaintext, key_hash, prefix = generate_api_key()
    device = Device(
        user_id=user.id,
        name=payload.name,
        api_key_hash=key_hash,
        api_key_prefix=prefix,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    # The plaintext key is returned exactly once.
    return DeviceCreated(**DeviceOut.model_validate(device).model_dump(), api_key=plaintext)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(device_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    device = await db.get(Device, device_id)
    if device is None or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
