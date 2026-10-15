import { WorkerEntrypoint } from "cloudflare:workers";
import binding from "virtual:sites-connector-preview";

// Destino local das chamadas. Cada requisição recebe seu próprio contexto.
export class ConnectorPreview extends WorkerEntrypoint {
  async getContext() {
    return binding.getContext?.() ?? { status: "binding_unavailable" };
  }

  async invoke(connectorId, actionName, args) {
    return binding.invoke(connectorId, actionName, args);
  }
}
export default { fetch() { return new Response("Not found", { status: 404 }); } };
