/**
 * Form Validation System
 * Real-time validation with visual feedback
 */

class FormValidator {
    constructor(form, options = {}) {
        this.form = typeof form === 'string' ? document.querySelector(form) : form;
        if (!this.form) return;

        this.options = {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessState: true,
            scrollToError: true,
            ...options
        };

        this.validators = {
            required: (value) => value.trim().length > 0,
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            minLength: (value, param) => value.length >= parseInt(param),
            maxLength: (value, param) => value.length <= parseInt(param),
            pattern: (value, param) => new RegExp(param).test(value),
            numeric: (value) => /^\d+$/.test(value),
            alpha: (value) => /^[a-zA-Z]+$/.test(value),
            alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(value),
            url: (value) => {
                try { new URL(value); return true; } catch { return false; }
            },
            date: (value) => !isNaN(Date.parse(value)),
            min: (value, param) => parseFloat(value) >= parseFloat(param),
            max: (value, param) => parseFloat(value) <= parseFloat(param),
            match: (value, param) => value === document.querySelector(`[name="${param}"]`)?.value
        };

        this.messages = {
            required: 'This field is required',
            email: 'Please enter a valid email address',
            minLength: 'Must be at least {param} characters',
            maxLength: 'Must be no more than {param} characters',
            pattern: 'Please match the required format',
            numeric: 'Please enter only numbers',
            alpha: 'Please enter only letters',
            alphanumeric: 'Please enter only letters and numbers',
            url: 'Please enter a valid URL',
            date: 'Please enter a valid date',
            min: 'Value must be at least {param}',
            max: 'Value must be no more than {param}',
            match: 'Fields do not match'
        };

        this.init();
    }

    init() {
        // Add validation classes to form
        this.form.classList.add('needs-validation');
        this.form.setAttribute('novalidate', '');

        // Find all inputs with validation attributes
        this.inputs = this.form.querySelectorAll('[data-validate], [required]');
        
        this.inputs.forEach(input => {
            // Create feedback elements
            this.createFeedbackElements(input);

            // Add event listeners
            if (this.options.validateOnBlur) {
                input.addEventListener('blur', () => this.validateInput(input));
            }

            if (this.options.validateOnInput) {
                input.addEventListener('input', () => {
                    // Debounce input validation
                    clearTimeout(input._validateTimeout);
                    input._validateTimeout = setTimeout(() => {
                        this.validateInput(input);
                    }, 300);
                });
            }
        });

        // Handle form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    createFeedbackElements(input) {
        const wrapper = input.closest('.form-group') || input.parentElement;
        
        // Add valid feedback element
        if (!wrapper.querySelector('.valid-feedback')) {
            const validFeedback = document.createElement('div');
            validFeedback.className = 'valid-feedback';
            validFeedback.textContent = 'Looks good!';
            wrapper.appendChild(validFeedback);
        }

        // Add invalid feedback element
        if (!wrapper.querySelector('.invalid-feedback')) {
            const invalidFeedback = document.createElement('div');
            invalidFeedback.className = 'invalid-feedback';
            wrapper.appendChild(invalidFeedback);
        }

        // Add strength meter for password fields
        if (input.type === 'password' && input.dataset.strengthMeter !== 'false') {
            this.addPasswordStrengthMeter(input);
        }

        // Add character counter if maxLength is set
        if (input.dataset.maxlength || input.maxLength > 0) {
            this.addCharacterCounter(input);
        }
    }

    addPasswordStrengthMeter(input) {
        const wrapper = input.closest('.form-group') || input.parentElement;
        if (wrapper.querySelector('.password-strength')) return;

        const meter = document.createElement('div');
        meter.className = 'password-strength';
        meter.innerHTML = `
            <div class="strength-bar">
                <div class="strength-fill"></div>
            </div>
            <span class="strength-text"></span>
        `;
        wrapper.appendChild(meter);

        input.addEventListener('input', () => {
            const strength = this.calculatePasswordStrength(input.value);
            this.updatePasswordStrengthMeter(meter, strength);
        });
    }

    calculatePasswordStrength(password) {
        let score = 0;
        if (!password) return { score: 0, label: '', class: '' };

        // Length
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;

        // Complexity
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^a-zA-Z0-9]/.test(password)) score++;

        if (score <= 2) return { score: 25, label: 'Weak', class: 'weak' };
        if (score <= 4) return { score: 50, label: 'Fair', class: 'fair' };
        if (score <= 5) return { score: 75, label: 'Good', class: 'good' };
        return { score: 100, label: 'Strong', class: 'strong' };
    }

    updatePasswordStrengthMeter(meter, strength) {
        const fill = meter.querySelector('.strength-fill');
        const text = meter.querySelector('.strength-text');
        
        fill.style.width = `${strength.score}%`;
        fill.className = `strength-fill ${strength.class}`;
        text.textContent = strength.label;
        text.className = `strength-text ${strength.class}`;
    }

    addCharacterCounter(input) {
        const wrapper = input.closest('.form-group') || input.parentElement;
        if (wrapper.querySelector('.char-counter')) return;

        const maxLength = parseInt(input.dataset.maxlength || input.maxLength);
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.innerHTML = `<span class="current">0</span>/<span class="max">${maxLength}</span>`;
        wrapper.appendChild(counter);

        input.addEventListener('input', () => {
            const current = input.value.length;
            counter.querySelector('.current').textContent = current;
            counter.classList.toggle('warning', current > maxLength * 0.8);
            counter.classList.toggle('error', current >= maxLength);
        });
    }

    validateInput(input) {
        const rules = this.getValidationRules(input);
        const value = input.value;
        let isValid = true;
        let errorMessage = '';

        for (const rule of rules) {
            const [ruleName, param] = rule.split(':');
            const validator = this.validators[ruleName];

            if (validator && !validator(value, param)) {
                isValid = false;
                errorMessage = this.messages[ruleName].replace('{param}', param);
                break;
            }
        }

        this.setInputState(input, isValid, errorMessage);
        return isValid;
    }

    getValidationRules(input) {
        const rules = [];

        // Check for required
        if (input.hasAttribute('required')) {
            rules.push('required');
        }

        // Check for data-validate attribute
        const validate = input.dataset.validate;
        if (validate) {
            rules.push(...validate.split('|'));
        }

        // Check for type-based validation
        if (input.type === 'email') {
            rules.push('email');
        }

        // Check for min/max length attributes
        if (input.minLength > 0) {
            rules.push(`minLength:${input.minLength}`);
        }
        if (input.maxLength > 0 && input.maxLength < 524288) {
            rules.push(`maxLength:${input.maxLength}`);
        }

        // Check for min/max value attributes
        if (input.min) {
            rules.push(`min:${input.min}`);
        }
        if (input.max) {
            rules.push(`max:${input.max}`);
        }

        // Check for pattern attribute
        if (input.pattern) {
            rules.push(`pattern:${input.pattern}`);
        }

        return rules;
    }

    setInputState(input, isValid, message = '') {
        const wrapper = input.closest('.form-group') || input.parentElement;
        const invalidFeedback = wrapper.querySelector('.invalid-feedback');

        input.classList.remove('is-valid', 'is-invalid');
        wrapper.classList.remove('was-validated', 'is-valid', 'is-invalid');

        if (input.value || !isValid) {
            wrapper.classList.add('was-validated');
            
            if (isValid) {
                if (this.options.showSuccessState) {
                    input.classList.add('is-valid');
                    wrapper.classList.add('is-valid');
                }
            } else {
                input.classList.add('is-invalid');
                wrapper.classList.add('is-invalid');
                if (invalidFeedback) {
                    invalidFeedback.textContent = message;
                }
            }
        }
    }

    handleSubmit(e) {
        let isFormValid = true;
        let firstInvalidInput = null;

        this.inputs.forEach(input => {
            const isValid = this.validateInput(input);
            if (!isValid && !firstInvalidInput) {
                firstInvalidInput = input;
                isFormValid = false;
            }
        });

        if (!isFormValid) {
            e.preventDefault();
            
            if (this.options.scrollToError && firstInvalidInput) {
                firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalidInput.focus();
            }

            // Show toast notification
            if (window.toast) {
                window.toast.error('Please fix the errors in the form');
            }
        }

        return isFormValid;
    }

    // Add custom validator
    addValidator(name, validator, message) {
        this.validators[name] = validator;
        this.messages[name] = message;
    }

    // Reset form validation state
    reset() {
        this.inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
            const wrapper = input.closest('.form-group') || input.parentElement;
            wrapper.classList.remove('was-validated', 'is-valid', 'is-invalid');
        });
    }
}

// Auto-initialize forms with data-validate-form attribute
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-validate-form]').forEach(form => {
        new FormValidator(form);
    });
});

// Export for manual initialization
window.FormValidator = FormValidator;

