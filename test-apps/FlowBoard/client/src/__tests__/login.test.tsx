import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "@/app/(auth)/login/page";

// =============================================================================
// Mock: useAuth from auth-context
//
// We mock the entire auth-context module so LoginPage receives a controlled
// login function. Each test can configure the mock's behavior independently.
// =============================================================================

const mockLogin = vi.fn();

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    login: mockLogin,
    user: null,
    loading: false,
    signup: vi.fn(),
    logout: vi.fn(),
  }),
  ApiError: class ApiError extends Error {
    status: number;
    errors?: Array<{ field: string; message: string }>;
    constructor(
      status: number,
      message: string,
      errors?: Array<{ field: string; message: string }>,
    ) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.errors = errors;
    }
  },
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockReset();
  });

  // ---------------------------------------------------------------------------
  // Test 1: Renders login form with all expected elements
  // ---------------------------------------------------------------------------
  it("renders email field, password field, submit button, and signup link", () => {
    render(<LoginPage />);

    // The heading -- "Sign in" appears in both the title and the button,
    // so we check by role to be specific
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(
      screen.getByText("Enter your credentials to access your workspace"),
    ).toBeInTheDocument();

    // Email input -- identified by label
    const emailInput = screen.getByLabelText("Email");
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toHaveAttribute("type", "email");
    expect(emailInput).toHaveAttribute("placeholder", "you@company.com");

    // Password input -- identified by label
    const passwordInput = screen.getByLabelText("Password");
    expect(passwordInput).toBeInTheDocument();
    expect(passwordInput).toHaveAttribute("type", "password");

    // Submit button
    const submitButton = screen.getByRole("button", { name: /sign in/i });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).toHaveAttribute("type", "submit");

    // Signup link
    const signupLink = screen.getByRole("link", { name: /create one/i });
    expect(signupLink).toHaveAttribute("href", "/signup");
  });

  // ---------------------------------------------------------------------------
  // Test 2: Shows validation errors when submitting an empty form
  // ---------------------------------------------------------------------------
  it("displays validation errors for empty email and password on submit", async () => {
    render(<LoginPage />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    fireEvent.click(submitButton);

    // Both field-level validation messages should appear
    await waitFor(() => {
      expect(screen.getByText("Email is required.")).toBeInTheDocument();
      expect(screen.getByText("Password is required.")).toBeInTheDocument();
    });

    // login() should NOT have been called because validation failed
    expect(mockLogin).not.toHaveBeenCalled();
  });

  // ---------------------------------------------------------------------------
  // Test 3: Calls login with entered credentials on valid submit
  // ---------------------------------------------------------------------------
  it("calls login function with email and password when form is valid", async () => {
    mockLogin.mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<LoginPage />);

    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    // Type valid credentials
    await user.type(emailInput, "test@flowboard.io");
    await user.type(passwordInput, "securePassword123");

    // Submit the form
    await user.click(submitButton);

    // The login function should have been called with the entered values
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledTimes(1);
      expect(mockLogin).toHaveBeenCalledWith(
        "test@flowboard.io",
        "securePassword123",
      );
    });
  });
});
