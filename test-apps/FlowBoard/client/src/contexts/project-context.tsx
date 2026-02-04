"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import api, { ApiError } from "@/lib/api";
import type { Project, ProjectMember } from "@/types";

// =============================================================================
// Project Context — provides current project data to all project sub-pages
// =============================================================================

interface ProjectContextValue {
  /** The currently-loaded project, or null if still loading / not found. */
  project: Project | null;
  /** Current user's membership record (includes role). */
  currentMember: ProjectMember | null;
  /** True while the initial project fetch is in-flight. */
  isLoading: boolean;
  /** Non-null if the project fetch failed. */
  error: string | null;
  /** HTTP status code of the failed request (e.g. 404, 403). */
  errorStatus: number | null;
  /** Re-fetch the project data from the API. */
  refetch: () => Promise<void>;
  /** Update local project state optimistically (e.g. after settings save). */
  setProject: (project: Project) => void;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

// -----------------------------------------------------------------------------
// Provider
// -----------------------------------------------------------------------------

interface ProjectProviderProps {
  projectId: string;
  children: ReactNode;
}

export function ProjectProvider({ projectId, children }: ProjectProviderProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [currentMember, setCurrentMember] = useState<ProjectMember | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);

  const fetchProject = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setErrorStatus(null);

    try {
      const res = await api.get<Project>(
        `/projects/${projectId}`,
      );
      setProject(res);
      // Server returns Project directly with members array, need to find current user's membership
      setCurrentMember(null); // TODO: Determine current member from response
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setErrorStatus(err.status);
      } else {
        setError("An unexpected error occurred.");
        setErrorStatus(500);
      }
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchProject();
  }, [fetchProject]);

  return (
    <ProjectContext.Provider
      value={{
        project,
        currentMember,
        isLoading,
        error,
        errorStatus,
        refetch: fetchProject,
        setProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

// -----------------------------------------------------------------------------
// Consumer hook
// -----------------------------------------------------------------------------

/**
 * Access the current project context. Must be used inside a `<ProjectProvider>`.
 */
export function useProjectContext(): ProjectContextValue {
  const ctx = useContext(ProjectContext);
  if (!ctx) {
    throw new Error(
      "useProjectContext must be used within a <ProjectProvider>.",
    );
  }
  return ctx;
}
