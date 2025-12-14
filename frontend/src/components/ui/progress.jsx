import * as React from "react"
import { cn } from "@/utils/cn"

const Progress = React.forwardRef(({ className, value, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-white/10",
      className
    )}
    {...props}
  >
    <div
      className="h-full bg-gradient-to-r from-primary to-secondary transition-all"
      style={{ width: `${value}%` }}
    />
  </div>
))
Progress.displayName = "Progress"

export { Progress }

