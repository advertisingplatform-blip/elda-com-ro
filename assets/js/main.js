(function(){
  var b=document.querySelector('.menu-btn'),n=document.getElementById('nav');
  if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)})}
  var q=document.getElementById('cauta');
  if(q){
    var secs=[].slice.call(document.querySelectorAll('.pcat')),emp=document.getElementById('fara-rezultate');
    q.addEventListener('input',function(){
      var t=q.value.trim().toLowerCase(),any=false;
      secs.forEach(function(s){var vis=0;
        [].forEach.call(s.querySelectorAll('tbody tr'),function(r){var m=!t||r.textContent.toLowerCase().indexOf(t)>-1;r.classList.toggle('hide',!m);if(m)vis++});
        s.classList.toggle('hide',!vis);if(vis)any=true});
      if(emp)emp.classList.toggle('hide',any);
    });
  }
})();
