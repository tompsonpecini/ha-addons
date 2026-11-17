// Corrige o "conectado, mas surdo" da Baileys 7.0.0-rc.9 (Evolution 2.3.7).
// Desde set/2026 o WhatsApp manda stanzas <status> que a Baileys nunca confirma (ack).
// Uns 50 min depois o servidor derruba o stream; ao reconectar, o mesmo <status>
// volta sem ack e a instância fica "open" sem receber nada.
// Ref.: evolution-foundation/evolution-api#2778, WhiskeySockets/Baileys#2858.
// Falha o build se a versão ou o ponto de inserção não forem os esperados.
const fs = require('fs');
const path = require('path');

const raiz = process.argv[2];
const versao = JSON.parse(fs.readFileSync(path.join(raiz, 'package.json'), 'utf8')).version;
if (versao !== '7.0.0-rc.9') {
  console.error(`Baileys ${versao}: patch feito para 7.0.0-rc.9; revise antes de aplicar.`);
  process.exit(1);
}

const arq = path.join(raiz, 'lib/Socket/messages-recv.js');
let src = fs.readFileSync(arq, 'utf8');
if (src.includes("'CB:status'")) {
  console.log('patch já aplicado');
  process.exit(0);
}

const ancora = "    ws.on('CB:notification', async (node) => {\n" +
  "        await processNode('notification', node, 'handling notification', handleNotification);\n" +
  "    });\n";
if (src.split(ancora).length !== 2) {
  console.error('ponto de inserção não encontrado (ou repetido) em ' + arq);
  process.exit(1);
}

const novo = ancora +
  "    ws.on('CB:status', (node) => {\n" +
  "        sendMessageAck(node).catch(error => onUnexpectedError(error, 'acking status stanza'));\n" +
  "    });\n";
fs.writeFileSync(arq, src.replace(ancora, novo));
console.log('patch CB:status aplicado em ' + arq);
