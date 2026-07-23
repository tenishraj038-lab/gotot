import React from "react";

// Mock framer-motion to avoid act() issues in test environment
const Div = React.forwardRef<HTMLDivElement, Record<string, unknown>>((props, ref) => {
  const { initial, animate, exit, whileHover, whileTap, whileInView, viewport, transition, variants, layout, layoutId, ...rest } = props;
  return <div ref={ref} {...rest} />;
});
Div.displayName = "MotionDiv";

const Section = React.forwardRef<HTMLElement, Record<string, unknown>>((props, ref) => {
  const { initial, animate, exit, whileHover, whileTap, whileInView, viewport, transition, variants, layout, layoutId, ...rest } = props;
  return <section ref={ref} {...rest} />;
});
Section.displayName = "MotionSection";

export const motion = {
  div: Div,
  section: Section,
  p: React.forwardRef<HTMLParagraphElement, Record<string, unknown>>((props, ref) => {
    const { initial, animate, exit, whileHover, whileTap, whileInView, viewport, transition, variants, layout, layoutId, ...rest } = props;
    return <p ref={ref} {...rest} />;
  }),
};

export const AnimatePresence = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export default { motion, AnimatePresence };
