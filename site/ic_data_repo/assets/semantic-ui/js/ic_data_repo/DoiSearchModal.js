import React, { useState } from "react";
import PropTypes from "prop-types";
import { Modal, Button, Form, Input, List, Message } from "semantic-ui-react";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import { http } from "react-invenio-forms";

export function DoiSearchModal({ trigger, onSelect }) {
  const [open, setOpen] = useState(false);
  const [doi, setDoi] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!doi) return;
    setLoading(true);
    setError(null);
    try {
      const response = await http.get("/api/symplectic/related-objects", {
        params: { doi },
      });
      const resultItems = response.data.results || [];
      setResults(resultItems);
      if (resultItems.length === 0) {
        setError("No related objects found for this DOI.");
      }
    } catch (e) {
      setError(e.response?.data?.message || e.message || "An error occurred.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setDoi("");
    setResults([]);
    setError(null);
    setLoading(false);
  };

  const handleSelect = (selectedItem) => {
    onSelect(selectedItem);
    handleClose();
  };

  return (
    <Modal
      onClose={handleClose}
      onOpen={() => setOpen(true)}
      open={open}
      trigger={trigger}
      closeIcon
    >
      <Modal.Header>{i18next.t("Find by DOI")}</Modal.Header>
      <Modal.Content>
        <Form onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
          <Form.Field>
            <Input
              action={{
                icon: "search",
                content: i18next.t("Search"),
                onClick: handleSearch,
                loading: loading,
                disabled: loading,
              }}
              placeholder="Enter DOI..."
              value={doi}
              onChange={(e) => setDoi(e.target.value)}
            />
          </Form.Field>
        </Form>
        {error && <Message negative>{error}</Message>}
        {results.length > 0 && (
          <List divided relaxed>
            <List.Header>{i18next.t("Search Results")}</List.Header>
            {results.map((item, index) => (
              <List.Item key={index}>
                <List.Content floated="right">
                  <Button primary size="tiny" onClick={() => handleSelect(item)}>
                    {i18next.t("Select")}
                  </Button>
                </List.Content>
                <List.Icon name="linkify" />
                <List.Content>
                  <List.Header>{item.title || i18next.t("No title available")}</List.Header>
                  <List.Description>
                    <strong>{i18next.t("DOI")}:</strong> {item.doi || i18next.t("N/A")}
                  </List.Description>
                </List.Content>
              </List.Item>
            ))}
          </List>
        )}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={handleClose}>{i18next.t("Close")}</Button>
      </Modal.Actions>
    </Modal>
  );
}

DoiSearchModal.propTypes = {
  trigger: PropTypes.node.isRequired,
  onSelect: PropTypes.func.isRequired,
};
