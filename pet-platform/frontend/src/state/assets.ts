import { useQuery } from "@tanstack/react-query";
import { Asset, AssetSchema } from "../api/client";

export function useAssets() {
  return useQuery<Asset[]>({
    queryKey: ["assets"],
    queryFn: async () => {
      const r = await fetch("/api/v1/assets");
      if (!r.ok) throw new Error("assets fetch failed");
      const raw = await r.json();
      return AssetSchema.array().parse(raw);
    },
  });
}
