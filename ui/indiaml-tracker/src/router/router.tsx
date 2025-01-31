import { createBrowserRouter, RouterProvider } from "react-router-dom";
import loadable from "@loadable/component";
// const Homepage = loadable(() => import("../views/Homepage"));


const V1Urls = {
  V2Homepage: loadable(() => import("../v1/Homepage"))
}


export const router = createBrowserRouter([
  {
    path: "/",
    element: <V1Urls.V2Homepage />,
    children: [
    ]
  },
]);