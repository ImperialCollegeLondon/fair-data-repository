import React, { Component } from "react";
import { Header, Grid, Label, List } from "semantic-ui-react";
import { humanReadableBytes } from "react-invenio-forms";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import PropTypes from "prop-types";

export class FileListContainer extends Component {
  render() {
    const { filesList, filesSize, filesEnabled, quota, decimalSizeDisplay } =
      this.props;
    return (
      <>
        {filesEnabled && (
          <Grid.Column mobile={16} tablet={10} computer={10} className="storage-col">
            <Header size="tiny" className="mr-10">
              {i18next.t("Storage available")}
            </Header>
            <List horizontal floated="right">
              <List.Item>
                <Label
                  {...(filesList.length === quota.maxFiles ? { color: "blue" } : {})}
                >
                  {i18next.t(`{{length}} out of {{maxfiles}} files`, {
                    length: filesList.length,
                    maxfiles: quota.maxFiles,
                  })}
                </Label>
              </List.Item>
              <List.Item>
                <Label
                  {...(humanReadableBytes(filesSize, decimalSizeDisplay) ===
                  humanReadableBytes(quota.maxStorage, decimalSizeDisplay)
                    ? { color: "blue" }
                    : {})}
                >
                  {humanReadableBytes(filesSize, decimalSizeDisplay)}{" "}
                  {i18next.t("out of")}{" "}
                  {humanReadableBytes(quota.maxStorage, decimalSizeDisplay)}
                </Label>
              </List.Item>
              <List.Item>
                <Label>
                  Size limit per file:{" "}
                  {humanReadableBytes(quota.maxFileSize, decimalSizeDisplay)}
                </Label>
              </List.Item>
            </List>
          </Grid.Column>
        )}
      </>
    );
  }
}

FileListContainer.propTypes = {
  filesList: PropTypes.array.isRequired,
  filesSize: PropTypes.number.isRequired,
  filesEnabled: PropTypes.bool.isRequired,
  quota: PropTypes.object.isRequired,
  decimalSizeDisplay: PropTypes.number.isRequired,
};
