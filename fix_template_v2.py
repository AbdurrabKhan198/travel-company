file_path = r'c:\Users\hp\Desktop\clients\travel company\Travel_agency\templates\base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The old broken section
old = '''                                    {% if od_wallet_days_remaining is not None and not od_wallet_is_expired %}
                                    <div class="text-xs text-gray-500 mt-1">{% if od_wallet_days_remaining == 0
                                        %}Expires Today{% elif od_wallet_days_remaining == 1 %}1 Day Left{% else %}{{
                                        od_wallet_days_remaining }} Days Left{% endif %}</div>
                                    {% endif %}
                            </div>
                            <a href="{% url 'wallet_history' %}?type=od"
                                class="block px-4 py-2 text-gray-700 hover:bg-sky-50 hover:text-sky-600 transition-colors">
                                <i class="fas fa-history mr-2 text-amber-500"></i> OD Wallet History
                            </a>
                            {% endif %}
                            <div class="px-4 py-2 bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-400">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="text-xs font-semibold text-gray-600">Cash Balance</span>
                                    <span class="text-xs font-bold text-blue-600">₹{{ cash_balance|floatformat:0
                                        }}</span>
                                </div>
                            </div>'''

# The new fixed section - all template tags on single lines
new = '''                                    {% if od_wallet_days_remaining is not None and not od_wallet_is_expired %}
                                    <div class="text-xs text-gray-500 mt-1">{% if od_wallet_days_remaining == 0 %}Expires Today{% elif od_wallet_days_remaining == 1 %}1 Day Left{% else %}{{ od_wallet_days_remaining }} Days Left{% endif %}</div>
                                    {% endif %}
                                </div>
                                <a href="{% url 'wallet_history' %}?type=od" class="block px-4 py-2 text-gray-700 hover:bg-sky-50 hover:text-sky-600 transition-colors">
                                    <i class="fas fa-history mr-2 text-amber-500"></i> OD Wallet History
                                </a>
                                {% endif %}
                                <div class="px-4 py-2 bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-400">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="text-xs font-semibold text-gray-600">Cash Balance</span>
                                        <span class="text-xs font-bold text-blue-600">₹{{ cash_balance|floatformat:0 }}</span>
                                    </div>
                                </div>'''

if old in content:
    content = content.replace(old, new)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Fixed the template!')
else:
    print('ERROR: Pattern not found')
    # Print lines 349-365 to debug
    lines = content.split('\n')
    for i, line in enumerate(lines[348:366], 349):
        print(f'{i}: {line[:80]}')
