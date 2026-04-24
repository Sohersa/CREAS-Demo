import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment, Stats } from "@react-three/drei";
import { Suspense, useMemo } from "react";
import Viewer from "../scene/Viewer";
import { useAssets } from "../state/assets";
import { useTelemetry } from "../state/telemetry";

export default function Twin() {
  const { data: assets } = useAssets();
  useTelemetry(); // subscribes to /api/v1/telemetry/stream
  const ready = useMemo(() => (assets?.length ?? 0) > 0, [assets]);

  return (
    <Canvas
      shadows
      camera={{ position: [62, 48, 58], fov: 45, near: 0.5, far: 500 }}
      gl={{ antialias: true, toneMappingExposure: 1.05 }}
      style={{ background: "#060D18" }}
    >
      <fog attach="fog" args={["#060D18", 80, 240]} />
      <hemisphereLight color="#7AAAC8" groundColor="#1A2A3A" intensity={0.55} />
      <directionalLight position={[40, 80, 30]} intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />
      <Suspense fallback={null}>
        <Environment preset="city" />
        {ready && <Viewer assets={assets!} />}
      </Suspense>
      <gridHelper args={[260, 52, "#1A2A3A", "#0F1D2E"]} position={[0, 0.02, 0]} />
      <OrbitControls target={[4, 2, -4]} enableDamping dampingFactor={0.08}
                     minDistance={15} maxDistance={160} maxPolarAngle={Math.PI * 0.48} />
      {import.meta.env.DEV && <Stats />}
    </Canvas>
  );
}
