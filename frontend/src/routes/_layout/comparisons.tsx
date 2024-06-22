import { ChakraProvider } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import MainLayout from "../../components/comparisons/Layout";

export const Route = createFileRoute("/_layout/comparisons")({
  component: ComparisonsHome,
});

function ComparisonsHome() {
  return (
    <ChakraProvider>
      <MainLayout />
    </ChakraProvider>
  );
}

export default ComparisonsHome;
