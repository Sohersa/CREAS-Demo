import { useRef, useState } from "react";
import { useGLTF } from "@react-three/drei";
import type { Mesh } from "three";
import type { Asset } from "../api/client";

/**
 * Loads the glTF for an asset. Meshopt/Draco loaders should be configured in
 * main.tsx. The onPick handler propagates to the selection store.
 *
 * In production, geometry is streamed via TileLoader.ts — this component
 * handles the "resident" case after a tile is landed.
 */
export default function AssetNode({ asset, onPick }: { asset: Asset; onPick: () => void }) {
  const ref = useRef<Mesh>(null);
  const [hover, setHover] = useState(false);
  const { scene } = useGLTF(asset.geometry.mesh_uri);

  return (
    <group
      position={[asset.position.x, asset.position.y, asset.position.z]}
      rotation={[asset.position.rx, asset.position.ry, asset.position.rz]}
      onClick={(e) => { e.stopPropagation(); onPick(); }}
      onPointerOver={() => setHover(true)}
      onPointerOut={() => setHover(false)}
    >
      <primitive object={scene.clone()} ref={ref} />
      {hover && <meshBasicMaterial attach="material" color="#FF5500" transparent opacity={0.18} />}
    </group>
  );
}
