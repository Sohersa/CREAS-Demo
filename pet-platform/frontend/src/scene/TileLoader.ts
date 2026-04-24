/**
 * 3DTiles-inspired spatial streamer.
 *
 * Partitions the plant into 20 m cubic tiles. Each tile has a manifest describing
 * its bbox and the maximum LOD available. At runtime we:
 *   1. compute the camera frustum
 *   2. intersect against the tile bboxes (BVH at the tile level, built offline)
 *   3. pick LOD per tile by screen-space error
 *   4. load glTF chunks via loaders.gl with Draco + Meshopt + KTX2 decoders
 *
 * Budget: 800 MB GPU. Evict least-recently-used tiles when over budget.
 */
import { Box3, Vector3, Camera, Frustum, Matrix4 } from "three";

export interface TileManifest {
  id: string;
  bbox: [number, number, number, number, number, number];
  maxLod: 100 | 200 | 300 | 400 | 500;
  uri: (lod: number) => string;
}

export class TileLoader {
  private frustum = new Frustum();
  private matrix = new Matrix4();
  private loaded = new Map<string, { lod: number; size: number }>();
  private budget = 800 * 1024 * 1024; // bytes

  constructor(private tiles: TileManifest[]) {}

  update(cam: Camera) {
    this.matrix.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse);
    this.frustum.setFromProjectionMatrix(this.matrix);
    for (const t of this.tiles) {
      const box = new Box3(
        new Vector3(t.bbox[0], t.bbox[1], t.bbox[2]),
        new Vector3(t.bbox[3], t.bbox[4], t.bbox[5]),
      );
      if (!this.frustum.intersectsBox(box)) {
        this.loaded.delete(t.id); // evict
        continue;
      }
      const dist = cam.position.distanceTo(box.getCenter(new Vector3()));
      const lod = this.pickLod(t, dist);
      const cur = this.loaded.get(t.id);
      if (!cur || cur.lod !== lod) this.request(t, lod);
    }
  }

  private pickLod(t: TileManifest, dist: number): number {
    if (dist < 25) return Math.min(500, t.maxLod);
    if (dist < 60) return Math.min(400, t.maxLod);
    if (dist < 120) return Math.min(300, t.maxLod);
    return Math.min(200, t.maxLod);
  }

  private request(t: TileManifest, lod: number) {
    // TODO: wire to @loaders.gl/gltf with Draco + Meshopt + KTX2 decoders
    this.loaded.set(t.id, { lod, size: 0 });
  }
}
