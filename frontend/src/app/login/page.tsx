"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { getAuthToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const setAuthModalOpen = useStore((s) => s.setAuthModalOpen);

  useEffect(() => {
    if (getAuthToken()) {
      router.replace("/dashboard");
    } else {
      setAuthModalOpen(true);
      router.replace("/");
    }
  }, [router, setAuthModalOpen]);

  return null;
}
