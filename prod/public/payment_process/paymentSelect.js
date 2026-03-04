eftbtn = document.getElementById('eftsecure-button');

currentCardbtn = document.getElementById('existing-card-option');
currentCardcontainer = document.getElementById('exisiting-card-details-container');

newCardbtn = document.getElementById('new-credit-card-option');
creditcardform = document.getElementById('credit-card-form');

paypalbtn = document.getElementById('paypal-button');

//dom content loaded event to retrieve GUID from local storage and display it on the page
document.addEventListener('DOMContentLoaded', function () {
  const guid = localStorage.getItem('guid');
  const last4Digits = localStorage.getItem('last4Digits');

  //if not found hide the current card option
  if (!last4Digits) {
    currentCardbtn.style.display = 'none';
  } else {
    const cardPlaceholder = document.getElementById('card-placeholder');
    cardPlaceholder.textContent = `Card Ending in ${last4Digits}`;
  }

  eftbtn.addEventListener('click', function () {
    window.location.href = 'eftsecure.html';
  });

  currentCardbtn.addEventListener('click', function () {
    creditcardform.style.display = 'none';
    currentCardcontainer.style.display = 'flex';
  });

  newCardbtn.addEventListener('click', function () {
    creditcardform.style.display = 'flex';
    currentCardcontainer.style.display = 'none';
  });

  paypalbtn.addEventListener('click', function () {
    window.location.href = 'paypal.html';
  });

});

