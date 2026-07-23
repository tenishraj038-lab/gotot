import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Features from "@/components/Features";

describe("Features", () => {
  it("renders without crashing", () => {
    const { container } = render(<Features />);
    expect(container).toBeTruthy();
  });
});
