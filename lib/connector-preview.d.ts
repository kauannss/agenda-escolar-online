declare module "virtual:sites-connector-preview" {
  const binding: import("./connector-contract.mjs").ConnectorBinding;
  export default binding;
}

// Somente a prévia local usa a variável de ambiente. Na publicação, cada requisição recebe o recurso por ctx.props.CONNECTORS.
declare namespace Cloudflare {
  interface Env {
    CONNECTORS?: import("./connector-contract.mjs").ConnectorBinding;
  }
}
