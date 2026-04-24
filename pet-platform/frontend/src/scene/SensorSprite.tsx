import { useEffect, useMemo, useRef } from "react";
import { CanvasTexture, Sprite, SpriteMaterial } from "three";
import type { Asset } from "../api/client";
import { useTelemetryValue } from "../state/telemetry";

/** Billboard showing the primary sensor of the asset. Canvas redraws on value change. */
export default function SensorSprite({ asset }: { asset: Asset }) {
  const ref = useRef<Sprite>(null);
  const primary = asset.sensors[0];
  const value = useTelemetryValue(primary?.tag ?? "");

  const { texture, canvas } = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 256; canvas.height = 84;
    const texture = new CanvasTexture(canvas);
    return { texture, canvas };
  }, []);

  useEffect(() => {
    if (!primary) return;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, 256, 84);
    ctx.fillStyle = "rgba(4,9,15,0.88)";
    ctx.beginPath(); (ctx as any).roundRect(0, 0, 256, 84, 10); ctx.fill();
    ctx.strokeStyle = "rgba(255,85,0,0.55)"; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "bold 18px monospace"; ctx.fillStyle = "#FF5500"; ctx.fillText(asset.tag, 12, 28);
    ctx.font = "13px monospace"; ctx.fillStyle = "#7AAAC8"; ctx.fillText(primary.kind, 12, 50);
    ctx.textAlign = "right"; ctx.font = "bold 22px monospace"; ctx.fillStyle = "#00C8F0";
    ctx.fillText(value != null ? value.toFixed(1) : "—", 228, 52);
    ctx.font = "11px monospace"; ctx.fillStyle = "#3A607A"; ctx.fillText(primary.unit, 244, 68);
    ctx.textAlign = "left";
    texture.needsUpdate = true;
  }, [value, primary, asset.tag, canvas, texture]);

  if (!primary) return null;

  return (
    <sprite ref={ref} position={[asset.position.x, asset.position.y + 6, asset.position.z]} scale={[4.2, 1.4, 1]}>
      <spriteMaterial attach="material" map={texture} depthTest={false} transparent />
    </sprite>
  );
}
