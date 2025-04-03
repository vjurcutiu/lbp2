// cypress/integration/conversation_spec.cy.js
describe('Conversation API End-to-End Tests', () => {
  it('retrieves the conversation list from the backend', () => {
    cy.request('GET', 'http://127.0.0.1:5000/conversation/list')
      .its('status')
      .should('eq', 200);
  });

  it('returns a conversation list payload with conversations property', () => {
    cy.request('GET', 'http://127.0.0.1:5000/conversation/list')
      .then((response) => {
        expect(response.body).to.have.property('conversations');
        // Optionally, if you know it should be an array:
        expect(response.body.conversations).to.be.an('array');
      });
  });
});
