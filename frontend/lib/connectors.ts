import { createConnectors } from "./connector-contract.mjs";
import { getConnectorBinding } from "./connector-context";

/** Mantém o contexto nesta requisição, sem compartilhar o cache entre visitantes. */
export function connectorsForRequest() {
  return createConnectors(getConnectorBinding());
}
export type {
  ConnectorContext,
  ConnectorResult,
  ConnectorFailureStatus,
  Json,
} from "./connector-contract.mjs";
