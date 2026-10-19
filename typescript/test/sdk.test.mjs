import test from 'node:test';
import assert from 'node:assert/strict';
import { Exogram, ExogramClient } from '../dist/index.mjs';

test('Exogram and ExogramClient exports are identical', () => {
    assert.strictEqual(ExogramClient, Exogram);
});

test('Zero-signup local mode initializes without API key', () => {
    const client = new ExogramClient();
    assert.strictEqual(client.localMode, true);
    assert.ok(client.getCurrentStateHash().startsWith('sha256:'));
});

test('Exogram client initializes with explicit apiKey or token', () => {
    const clientA = new Exogram({ token: 'exo_test_12345', apiUrl: 'https://api.exogram.ai' });
    assert.strictEqual(clientA.localMode, false);

    const clientB = new ExogramClient({ apiKey: 'exo_test_67890', baseUrl: 'https://exogram.ai' });
    assert.strictEqual(clientB.localMode, false);
});

test('Sub-clients vault, neuralNetwork, governance, and actions work end-to-end in local mode', async () => {
    const client = new ExogramClient({ localMode: true });

    const r1 = await client.vault.store('Deploy target is Cloudflare Workers us-east', {
        namespace: 'work',
        sphere: 'Work',
        confidence: 0.95
    });
    assert.ok(r1.id.startsWith('mem_'));
    assert.ok(r1.stateHash.startsWith('sha256:'));

    const r2 = await client.vault.store('Cloudflare Workers uses OpenNext adapter for production', {
        namespace: 'work',
        sphere: 'Work',
        confidence: 0.93
    });
    assert.notStrictEqual(r2.stateHash, r1.stateHash);

    // Scalar conflict supersession
    const r3 = await client.vault.store('Deploy target is Cloudflare Workers Global Edge', {
        namespace: 'work',
        sphere: 'Work',
        confidence: 0.98
    });
    assert.strictEqual(r3.conflictsSuperseded, 1);

    const hits = await client.vault.search('Cloudflare Workers', { namespace: 'work', spheres: ['Work'], topK: 5 });
    assert.ok(hits.length >= 2);
    assert.ok(hits.some(h => h.content.includes('Global Edge')));

    const packet = await client.neuralNetwork.retrieve('What adapter powers production?', {
        spheres: ['Work', 'People', 'Life'],
        maxHops: 4
    });
    assert.strictEqual(packet.pprConverged, true);
    assert.ok(packet.claims.length >= 1);
    assert.ok(packet.entities.length >= 1);

    const judgment = await client.governance.evaluateAction({
        agentId: 'ts-agent',
        actionType: 'deploy_worker',
        parameters: { target: 'cloudflare' },
        stateHash: packet.stateHash
    });
    assert.strictEqual(judgment.permitted, true);
    assert.ok(judgment.executionToken?.startsWith('exo_tok_'));
    assert.strictEqual(judgment.latencyMs, 0.07);

    const receipt = await client.actions.execute(judgment.executionToken);
    assert.strictEqual(receipt.committed, true);
    assert.ok(receipt.ledgerHash.startsWith('sha256:'));
});

test('Governance blocks stale stateHash and destructive commands', async () => {
    const client = new ExogramClient({ localMode: true });

    const stale = await client.governance.evaluateAction(
        'rogue-agent',
        'update_schema',
        { table: 'memories' },
        'STALE_STATE_HASH'
    );
    assert.strictEqual(stale.permitted, false);
    assert.ok(stale.reason.includes('STATE_HASH_DRIFT'));

    const destructive = await client.governance.evaluateAction({
        agentId: 'rogue-agent',
        actionType: 'sql_exec',
        parameters: { query: 'DROP TABLE memories;' }
    });
    assert.strictEqual(destructive.permitted, false);
    assert.ok(destructive.reason.includes('BLOCKED_BY_INSTINCT'));
});
