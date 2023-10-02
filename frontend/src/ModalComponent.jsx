import React, { useState } from 'react';
import Modal from 'react-modal';
import sampleInvoice from './3.jpeg'

function SampleImageComponent(props) {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  const openModal = () => {
    setModalIsOpen(true);
  };

  const closeModal = () => {
    setModalIsOpen(false);
  };

  return (
    <div style={props.style}>
      <h5 style={{ marginTop: -50 }}>Make sure your image is upright!</h5>
     

      <Modal
        isOpen={modalIsOpen}
        onRequestClose={closeModal}
        contentLabel="Sample Image Modal"
      >
        <div>
            <h5>Make sure the invoice you upload is the same orientation as this sample image</h5>
          
        </div>
      </Modal>
    </div>
  );
}

export default SampleImageComponent;
