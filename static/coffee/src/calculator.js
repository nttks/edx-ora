// Generated by CoffeeScript 1.3.3
(function() {

  this.Calculator = (function() {

    function Calculator() {
      $('.calc').click(this.toggle);
      $('form#calculator').submit(this.calculate).submit(function(e) {
        return e.preventDefault();
      });
      $('div.help-wrapper a').hover(this.helpToggle).click(function(e) {
        return e.preventDefault();
      });
    }

    Calculator.prototype.toggle = function() {
      $('li.calc-main').toggleClass('open');
      $('#calculator_wrapper #calculator_input').focus();
      if ($('.calc.closed').length) {
        $('.calc').attr('aria-label', 'Open Calculator');
      } else {
        $('.calc').attr('aria-label', 'Close Calculator');
      }
      return $('.calc').toggleClass('closed');
    };

    Calculator.prototype.helpToggle = function() {
      return $('.help').toggleClass('shown');
    };

    Calculator.prototype.calculate = function() {
      return $.getWithPrefix('/calculate', {
        equation: $('#calculator_input').val()
      }, function(data) {
        return $('#calculator_output').val(data.result);
      });
    };

    return Calculator;

  })();

}).call(this);