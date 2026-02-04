"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";

// =============================================================================
// Project Types
// =============================================================================

export interface ProjectMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  ownerId: string;
  members: ProjectMember[];
  taskCounts?: {
    total: number;
    completed: number;
  };
  createdAt: string;
  updatedAt: string;
}

// Server returns Project[] directly, no wrapper

interface UseProjectsReturn {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// =============================================================================
// useProjects -- Fetch and cache the user's project list
// =============================================================================

export function useProjects(): UseProjectsReturn {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await api.get<Project[]>("/projects");
      setProjects(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load projects");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!fetchedRef.current) {
      fetchedRef.current = true;
      fetchProjects();
    }
  }, [fetchProjects]);

  return { projects, isLoading, error, refetch: fetchProjects };
}
