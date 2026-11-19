i built Antibody Guard, an immune system for AI agents’ money and memory, on Reactive Network.

one poisoned email saying “updated bank details” can plant a lie in an agent’s memory and send its money to an attacker.

with Antibody Guard, the agent can only propose a payment. it never signs one. GuardVault checks the payee, label, cap, daily limit and duplicates on-chain.

GuardReactive watches vaults across Base Sepolia and Ethereum Sepolia. catch an attacker once, quarantine it everywhere. new vaults start immune. no server, no keeper, no human in the loop. median reaction: about 2 seconds.

every memory carries its source. once an attacker is identified, everything it planted becomes unusable. that took 8 seconds in the live run.

in another run, an AI risk scorer flagged a phishing email sent through Claude at 95. the report went on-chain and the address was quarantined across all 7 guarded contracts in under 30 seconds. the model can only restrict. it never pays or unfreezes.

connect through Claude, the SDK (`npm i antibody-guard`), the MCP server (`npx antibody-guard-mcp`) or the public API.

fooled once. never twice.

Claude connector: https://antibody-guard-reactive.netlify.app/mcp
live app: https://antibody-guard-reactive.netlify.app
code: https://github.com/linoxbt/Antibody-gaurd
