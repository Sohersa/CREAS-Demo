import { z } from "zod";

export const PositionSchema = z.object({
  x: z.number(), y: z.number(), z: z.number(),
  rx: z.number().default(0), ry: z.number().default(0), rz: z.number().default(0),
  scale: z.number().default(1),
});

export const GeometrySchema = z.object({
  mesh_uri: z.string(),
  lod: z.number().int().min(100).max(600).default(500),
  bbox: z.tuple([z.number(), z.number(), z.number(), z.number(), z.number(), z.number()]),
});

export const SensorRefSchema = z.object({
  tag: z.string(),
  kind: z.string(),
  unit: z.string(),
  threshold_low: z.number().optional(),
  threshold_high: z.number().optional(),
});

export const AssetSchema = z.object({
  id: z.string(),
  tag: z.string(),
  name: z.string(),
  cls: z.string(),
  parent_id: z.string().optional().nullable(),
  geometry: GeometrySchema,
  position: PositionSchema,
  sensors: z.array(SensorRefSchema).default([]),
  state: z.enum(["operating", "idle", "alarm", "maintenance", "offline"]).default("operating"),
  updated_at: z.string(),
});

export type Asset = z.infer<typeof AssetSchema>;
