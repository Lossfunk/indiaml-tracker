import { createBrowserRouter, RouterProvider } from "react-router-dom";
import loadable from "@loadable/component";
// const Homepage = loadable(() => import("../views/Homepage"));


const V1Urls = {
  V2Homepage: loadable(() => import("../v1/Homepage")),
  NeurIPS2024: loadable(() => import("../v1/neurips-2024"))
}


export const router = createBrowserRouter([
  {
    path: "/",
    element: <V1Urls.V2Homepage />,
    children: [
      {
        path: "neurips-2024",
        element: <V1Urls.NeurIPS2024   />
      }
    ]
  },
]);