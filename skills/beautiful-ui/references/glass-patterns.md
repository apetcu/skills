# Glass Patterns

Advanced glassmorphism component recipes for dark-mode Next.js interfaces.

## Table of Contents

- Glass Modal / Dialog
- Glass Sidebar
- Glass Tabs
- Glass Data Table
- Glass Tooltip
- Glass Select / Dropdown
- Glass Toast Notification
- Glass Skeleton Loading
- Glass Hero Section
- Layering Rules

---

## Glass Modal / Dialog

```tsx
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { motion, AnimatePresence } from "framer-motion";

export function GlassDialog({ open, onOpenChange, children, title }) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open && (
          <DialogPrimitive.Portal forceMount>
            {/* Overlay */}
            <DialogPrimitive.Overlay asChild>
              <motion.div
                className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              />
            </DialogPrimitive.Overlay>

            {/* Content */}
            <DialogPrimitive.Content asChild>
              <motion.div
                className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white/[0.08] backdrop-blur-2xl backdrop-saturate-150 border border-white/[0.12] shadow-[0_24px_80px_rgba(0,0,0,0.5)] p-6"
                initial={{ opacity: 0, scale: 0.95, y: "-48%", x: "-50%" }}
                animate={{ opacity: 1, scale: 1, y: "-50%", x: "-50%" }}
                exit={{ opacity: 0, scale: 0.97, y: "-48%", x: "-50%" }}
                transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              >
                {/* Top edge highlight */}
                <div className="absolute inset-x-0 top-0 h-px rounded-t-2xl bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                <DialogPrimitive.Title className="text-lg font-semibold text-foreground mb-4">
                  {title}
                </DialogPrimitive.Title>
                {children}
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        )}
      </AnimatePresence>
    </DialogPrimitive.Root>
  );
}
```

## Glass Sidebar

```tsx
export function GlassSidebar({ children }) {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/[0.08] bg-background/40 backdrop-blur-2xl">
      {/* Logo area */}
      <div className="flex h-16 items-center border-b border-white/[0.08] px-6">
        <span className="text-lg font-bold text-foreground">Logo</span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 space-y-1 p-3">
        {children}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-white/[0.08] p-4">
        {/* User avatar / settings */}
      </div>
    </aside>
  );
}

export function SidebarItem({ icon: Icon, label, active = false }) {
  return (
    <button
      className={cn(
        "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
        active
          ? "bg-white/[0.1] text-foreground shadow-[inset_0_0.5px_0_rgba(255,255,255,0.1)]"
          : "text-foreground-muted hover:bg-white/[0.06] hover:text-foreground"
      )}
    >
      <Icon className="size-5 shrink-0" />
      {label}
    </button>
  );
}
```

## Glass Tabs

```tsx
import * as TabsPrimitive from "@radix-ui/react-tabs";

export function GlassTabs({ tabs, defaultValue }) {
  return (
    <TabsPrimitive.Root defaultValue={defaultValue}>
      <TabsPrimitive.List className="inline-flex items-center gap-1 rounded-xl bg-white/[0.04] p-1 border border-white/[0.08]">
        {tabs.map((tab) => (
          <TabsPrimitive.Trigger
            key={tab.value}
            value={tab.value}
            className="rounded-lg px-4 py-2 text-sm font-medium text-foreground-muted transition-all duration-150 data-[state=active]:bg-white/[0.1] data-[state=active]:text-foreground data-[state=active]:shadow-[inset_0_0.5px_0_rgba(255,255,255,0.15)]"
          >
            {tab.label}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>

      {tabs.map((tab) => (
        <TabsPrimitive.Content key={tab.value} value={tab.value} className="mt-4">
          {tab.content}
        </TabsPrimitive.Content>
      ))}
    </TabsPrimitive.Root>
  );
}
```

## Glass Data Table

```tsx
export function GlassTable({ columns, data }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-xl">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/[0.08]">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-foreground-muted"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className="border-b border-white/[0.04] transition-colors hover:bg-white/[0.04]"
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-sm text-foreground">
                  {row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## Glass Tooltip

```tsx
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

export function GlassTooltip({ children, content }) {
  return (
    <TooltipPrimitive.Provider delayDuration={200}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Content
          className="z-50 rounded-lg bg-white/[0.12] backdrop-blur-xl border border-white/[0.15] px-3 py-1.5 text-xs text-foreground shadow-[0_8px_32px_rgba(0,0,0,0.3)] animate-scale-in"
          sideOffset={6}
        >
          {content}
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
```

## Glass Select / Dropdown

```tsx
export function GlassSelect({ options, value, onChange, placeholder }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "flex h-11 w-full appearance-none rounded-xl px-4 pr-10 text-sm",
          "bg-white/[0.06] backdrop-blur-lg",
          "border border-white/[0.1]",
          "text-foreground",
          "focus:outline-none focus:border-white/[0.25] focus:ring-2 focus:ring-accent/30",
          "transition-all duration-200"
        )}
      >
        {placeholder && (
          <option value="" className="bg-surface text-foreground-muted">
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-surface text-foreground">
            {opt.label}
          </option>
        ))}
      </select>
      {/* Chevron */}
      <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-foreground-muted">
        <ChevronDown className="size-4" />
      </div>
    </div>
  );
}
```

## Glass Toast Notification

```tsx
import { motion } from "framer-motion";

export function GlassToast({ message, type = "info", onDismiss }) {
  const accentMap = {
    info: "border-l-accent",
    success: "border-l-success",
    warning: "border-l-warning",
    error: "border-l-destructive",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.95, filter: "blur(4px)" }}
      animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
      exit={{ opacity: 0, y: -8, scale: 0.97, filter: "blur(4px)" }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "rounded-xl bg-white/[0.08] backdrop-blur-2xl border border-white/[0.12] border-l-2 px-4 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
        accentMap[type]
      )}
    >
      <p className="text-sm text-foreground">{message}</p>
    </motion.div>
  );
}
```

## Glass Skeleton Loading

```tsx
export function GlassSkeleton({ className }) {
  return (
    <div
      className={cn(
        "rounded-xl bg-white/[0.04]",
        "bg-[length:200%_100%] animate-shimmer",
        "bg-gradient-to-r from-white/[0.04] via-white/[0.08] to-white/[0.04]",
        className
      )}
    />
  );
}

// Usage
<div className="space-y-4">
  <GlassSkeleton className="h-8 w-48" />
  <GlassSkeleton className="h-4 w-full" />
  <GlassSkeleton className="h-4 w-3/4" />
  <GlassSkeleton className="h-32 w-full" />
</div>
```

## Glass Hero Section

```tsx
export function GlassHero({ title, subtitle, cta }) {
  return (
    <section className="relative flex min-h-[80vh] items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="text-center"
      >
        <motion.h1
          className="font-display text-5xl font-bold tracking-tight text-foreground sm:text-7xl"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        >
          {title}
        </motion.h1>

        <motion.p
          className="mx-auto mt-6 max-w-xl text-lg text-foreground-muted leading-relaxed"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          {subtitle}
        </motion.p>

        <motion.div
          className="mt-10"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <GlassButton variant="accent" size="lg">
            {cta}
          </GlassButton>
        </motion.div>
      </motion.div>
    </section>
  );
}
```

## Layering Rules

Glass surfaces must be layered correctly to create depth:

```
Background (gradient orbs + noise)     z-[-10]
  └── Surface 1 (page glass)           bg-white/[0.03]  blur-lg
       └── Surface 2 (card glass)      bg-white/[0.06]  blur-xl
            └── Surface 3 (elevated)   bg-white/[0.10]  blur-2xl
                 └── Popover/Modal     bg-white/[0.12]  blur-2xl
```

**Key rules:**
- Each layer increases white opacity by ~0.03-0.04
- Each layer increases blur strength
- Borders get slightly more visible per layer
- Never stack more than 3 glass layers (performance + visual clarity)
- Top highlight (1px gradient) on the topmost glass layer only
- Deep shadows on floating elements (modals, dropdowns, tooltips)
