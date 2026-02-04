import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Input — FlowBoard Design System
 *
 * Base: surface-elevated background, edge-default border
 * Focus: brand violet ring
 * Error: red border + red ring
 * Disabled: reduced opacity, not-allowed cursor
 * Sizes: sm (28px), md (36px)
 */
const inputVariants = cva(
  [
    "flex w-full rounded-md font-body",
    "bg-surface-elevated",
    "border border-input",
    "text-text-primary",
    "ring-offset-background",
    "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-text-primary",
    "placeholder:text-text-quaternary",
    "transition-colors duration-fast",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed disabled:opacity-50",
  ].join(" "),
  {
    variants: {
      inputSize: {
        sm: "h-7 px-2.5 text-xs",
        md: "h-9 px-3 text-sm",
      },
      error: {
        true: "border-error focus-visible:ring-error",
        false: "",
      },
    },
    defaultVariants: {
      inputSize: "md",
      error: false,
    },
  }
);

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof inputVariants> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, inputSize, error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(inputVariants({ inputSize, error, className }))}
        ref={ref}
        aria-invalid={error ? true : undefined}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input, inputVariants };
