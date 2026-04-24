import { create } from "zustand";

interface SelectionStore {
  selectedId: string | null;
  select: (id: string | null) => void;
}

export const useSelection = create<SelectionStore>((set) => ({
  selectedId: null,
  select: (id) => set({ selectedId: id }),
}));
