import { useMemo } from "react";
import AssetNode from "./AssetNode";
import SensorSprite from "./SensorSprite";
import type { Asset } from "../api/client";
import { useSelection } from "../state/selection";

export default function Viewer({ assets }: { assets: Asset[] }) {
  const grouped = useMemo(() => {
    const m: Record<string, Asset[]> = {};
    for (const a of assets) (m[a.cls] ??= []).push(a);
    return m;
  }, [assets]);
  const { select } = useSelection();

  return (
    <group>
      {assets.map(a => (
        <AssetNode key={a.id} asset={a} onPick={() => select(a.id)} />
      ))}
      {assets.filter(a => a.sensors?.length).map(a => (
        <SensorSprite key={`s-${a.id}`} asset={a} />
      ))}
    </group>
  );
}
