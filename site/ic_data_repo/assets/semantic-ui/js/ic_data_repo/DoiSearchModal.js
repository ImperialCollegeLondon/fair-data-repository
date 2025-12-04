import React, { useState } from "react";
import PropTypes from "prop-types";
import { Modal, Button, Form, Input, List, Message, Pagination } from "semantic-ui-react";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import { http } from "react-invenio-forms";

export function DoiSearchModal({ trigger, onSelect }) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState("doi");
  const [results, setResults] = useState([]);
  // pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5; // adjust page size as needed

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!searchQuery) return;
    setLoading(true);
    setError(null);
    try {
      const response = await http.get("/api/symplectic/related-publications", {
        params: { search_query: searchQuery, search_type: searchType },
      });
      const resultItems = response.data.results || [];
      setResults(resultItems);
      setCurrentPage(1);
      if (resultItems.length === 0) {
        setError(i18next.t("No related objects found for this search."));
      }
    } catch (e) {
      setError(e.response?.data?.message || e.message || i18next.t("An error occurred."));
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSearchQuery("");
    setSearchType("doi");
    setResults([]);
    setError(null);
    setLoading(false);
  };

  const handleSelect = (selectedItem) => {
    onSelect(selectedItem.doi);
    handleClose();
  };

  const searchOptions = [
    { key: "title-keywords", value: "title-keywords", text: i18next.t("Title") },
    { key: "first-author-name", value: "first-author-name", text: i18next.t("Author") },
  ];

  return (
    <Modal
      onClose={handleClose}
      onOpen={() => setOpen(true)}
      open={open}
      trigger={trigger}
      closeIcon
    >
      <Modal.Header>{i18next.t("Find related objects")}</Modal.Header>
      <Modal.Content>
        <Form onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
          <Form.Group widths="equal">
            <Form.Select
              width={6}
              fluid
              size="small"
              label={i18next.t("Search type")}
              options={searchOptions}
              value={searchType}
              onChange={(e, { value }) => setSearchType(value)}
              disabled={loading}
              placeholder={searchOptions[0].text}
            />
            <Form.Field width={10}>
              <label htmlFor="doi-search-input">{i18next.t("Search")}</label>
              <Input
                id="doi-search-input"
                aria-describedby="doi-search-help"
                action={{
                  icon: "search",
                  content: i18next.t("Search"),
                  onClick: handleSearch,
                  loading: loading,
                  disabled: loading,
                }}
                placeholder={
                  i18next.t("Enter keywords...")
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </Form.Field>
          </Form.Group>

          {/* Help text for controls */}
          <Form.Field>
            <Message info size="mini" id="doi-search-help">
              <>
                {i18next.t(
                  "You can search for existing publications by title, author name and it will query"
                )}{" "}
                <a
                  href="https://www.imperial.ac.uk/research-and-innovation/support-for-staff/scholarly-communication/symplectic/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {i18next.t("symplectic elements")}
                </a>
                {". "}{i18next.t("for related works.")}
              </>
            </Message>
          </Form.Field>
        </Form>

        {error && <Message negative>{error}</Message>}

        {results.length > 0 && (
          <>
            <List divided relaxed>
              <List.Header>{i18next.t("Search Results")}</List.Header>
              {/*
                client-side pagination: compute slice for current page
              */}
              {results
                .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                .map((item, index) => (
                  <List.Item key={item.doi || item.id || `${(currentPage - 1) * pageSize + index}`}>
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

            {results.length > pageSize && (
              <div style={{ display: "flex", justifyContent: "center", marginTop: "0.5rem" }}>
                <Pagination
                  activePage={currentPage}
                  totalPages={Math.ceil(results.length / pageSize)}
                  onPageChange={(e, { activePage }) => setCurrentPage(activePage)}
                  size="small"
                />
              </div>
            )}
          </>
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
  onSelect: PropTypes.func,
};
