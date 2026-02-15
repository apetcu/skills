# Animation Recipes

Framer Motion orchestration patterns for glassmorphism interfaces.

## Table of Contents

- Easing Reference
- Page Load Orchestration
- Scroll-Triggered Reveals
- Shared Layout Animations
- Morphing Glass Containers
- Particle / Orb Animations
- Number Counter
- Reduced Motion

---

## Easing Reference

```ts
// Use this custom easing for all glass UI animations
const glassEase = [0.16, 1, 0.3, 1]; // fast-out, slow-in (expo-like)

// Spring presets
const springSnappy = { type: "spring", stiffness: 400, damping: 25, mass: 0.8 };
const springGentle = { type: "spring", stiffness: 200, damping: 20, mass: 1 };
const springBouncy = { type: "spring", stiffness: 300, damping: 15, mass: 0.8 };
```

## Page Load Orchestration

Full page entrance with staggered reveal:

```tsx
const pageVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05,
    },
  },
};

const sectionVariants = {
  hidden: { opacity: 0, y: 24, filter: "blur(6px)" },
  show: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
  },
};

export function PageLayout({ children }) {
  return (
    <motion.div variants={pageVariants} initial="hidden" animate="show">
      <motion.header variants={sectionVariants}>
        {/* navbar */}
      </motion.header>
      <motion.section variants={sectionVariants}>
        {/* hero */}
      </motion.section>
      <motion.section variants={sectionVariants}>
        {/* content */}
      </motion.section>
    </motion.div>
  );
}
```

## Scroll-Triggered Reveals

Use `whileInView` for elements that appear on scroll:

```tsx
export function ScrollReveal({ children, className }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32, filter: "blur(4px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// Stagger a group of cards on scroll
export function ScrollStaggerGrid({ children }) {
  return (
    <motion.div
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: 0.08 } },
      }}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      {React.Children.map(children, (child) => (
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 20, filter: "blur(4px)" },
            show: {
              opacity: 1, y: 0, filter: "blur(0px)",
              transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
            },
          }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
}
```

## Shared Layout Animations

Smooth transitions between states using `layoutId`:

```tsx
// Tab indicator that morphs between tabs
export function AnimatedTabs({ tabs, activeTab, onChange }) {
  return (
    <div className="flex gap-1 rounded-xl bg-white/[0.04] p-1 border border-white/[0.08]">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className="relative rounded-lg px-4 py-2 text-sm font-medium text-foreground-muted transition-colors"
        >
          {activeTab === tab.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute inset-0 rounded-lg bg-white/[0.1] shadow-[inset_0_0.5px_0_rgba(255,255,255,0.15)]"
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
            />
          )}
          <span className="relative z-10">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}
```

## Morphing Glass Containers

Smooth resize when content changes:

```tsx
export function GlassExpandable({ expanded, children, preview }) {
  return (
    <motion.div
      layout
      className="overflow-hidden rounded-2xl bg-white/[0.06] backdrop-blur-xl border border-white/[0.12]"
      transition={{ layout: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } }}
    >
      <div className="p-6">{preview}</div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="border-t border-white/[0.08] px-6 pb-6 pt-4"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
```

## Particle / Orb Animations

Floating background orbs that drift slowly:

```tsx
export function FloatingOrbs() {
  const orbs = [
    { size: 400, color: "oklch(45% 0.15 270)", x: "10%", y: "20%", delay: 0 },
    { size: 300, color: "oklch(50% 0.18 200)", x: "70%", y: "60%", delay: 2 },
    { size: 250, color: "oklch(55% 0.16 320)", x: "40%", y: "80%", delay: 4 },
  ];

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-background">
      {orbs.map((orb, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: orb.size,
            height: orb.size,
            background: orb.color,
            left: orb.x,
            top: orb.y,
            filter: `blur(${orb.size * 0.3}px)`,
            opacity: 0.25,
          }}
          animate={{
            x: [0, 30, -20, 0],
            y: [0, -25, 15, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
            delay: orb.delay,
          }}
        />
      ))}
    </div>
  );
}
```

## Number Counter

Animated counting for stats and metrics:

```tsx
import { useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect } from "react";

export function AnimatedCounter({ from = 0, to, duration = 1.5 }) {
  const count = useMotionValue(from);
  const rounded = useTransform(count, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(count, to, {
      duration,
      ease: [0.16, 1, 0.3, 1],
    });
    return controls.stop;
  }, [to]);

  return (
    <motion.span className="tabular-nums font-display text-4xl font-bold text-foreground">
      {rounded}
    </motion.span>
  );
}
```

## Reduced Motion

Always wrap non-essential animations in a reduced-motion check:

```tsx
import { useReducedMotion } from "framer-motion";

export function useGlassAnimation() {
  const shouldReduce = useReducedMotion();

  return {
    initial: shouldReduce ? {} : { opacity: 0, y: 20, filter: "blur(4px)" },
    animate: { opacity: 1, y: 0, filter: "blur(0px)" },
    transition: shouldReduce
      ? { duration: 0 }
      : { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  };
}

// Usage
function MyComponent() {
  const anim = useGlassAnimation();
  return <motion.div {...anim}>Content</motion.div>;
}
```

Also add this global CSS as a fallback:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
