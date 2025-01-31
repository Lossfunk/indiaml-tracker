import { createContext } from "react";
import { RoughSVG } from "roughjs/bin/svg";

export const RoughSVGContext = createContext<RoughSVG | null>(null);