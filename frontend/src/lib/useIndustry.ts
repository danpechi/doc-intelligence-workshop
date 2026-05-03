"use client";

import { useCallback, useEffect, useState } from "react";
import { type IndustryKey, INDUSTRIES } from "./industryConfig";

const STORAGE_KEY = "ai_workshop_industry";
const DEFAULT: IndustryKey = "fins";

export function useIndustry() {
  const [industry, setIndustryState] = useState<IndustryKey>(DEFAULT);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as IndustryKey | null;
      if (saved && INDUSTRIES[saved]) setIndustryState(saved);
    } catch {}
    setLoaded(true);
  }, []);

  const setIndustry = useCallback((key: IndustryKey) => {
    setIndustryState(key);
    try {
      localStorage.setItem(STORAGE_KEY, key);
    } catch {}
  }, []);

  return { industry, config: INDUSTRIES[industry], setIndustry, loaded };
}
