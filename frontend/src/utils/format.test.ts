import { describe, expect, it } from "vitest";
import { formatCompact, formatDuration, formatNumber } from "./format";

describe("format", () => {
  it("formate les nombres à la française avec des espaces simples", () => {
    expect(formatNumber(1587159)).toBe("1 587 159");
    expect(formatNumber(0)).toBe("0");
  });

  it("abrège les grands nombres", () => {
    expect(formatCompact(6_349_935)).toBe("6,3 M");
  });

  it("formate les durées", () => {
    expect(formatDuration(65)).toBe("1 min 05 s");
    expect(formatDuration(3780)).toBe("1 h 03 min");
    expect(formatDuration(-5)).toBe("0 min 00 s");
  });
});
