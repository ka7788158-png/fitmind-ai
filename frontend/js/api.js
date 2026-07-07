const API_BASE = 'http://127.0.0.1:8000';

const API = {
  async generateDailyPlan(memberId, profile, dayNumber, dayName) {
    const res = await fetch(`${API_BASE}/generate-daily-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member_id: memberId, profile, day_number: dayNumber, day_name: dayName })
    });
    return res.json();
  },

  async modifyPlan(currentPlan, request, profile) {
    const res = await fetch(`${API_BASE}/modify-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_plan: currentPlan, request, profile })
    });
    return res.json();
  },

  async chat(memberId, question, history) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member_id: memberId, question, history })
    });
    return res.json();
  },

  async generatePlan(profile) {
    const res = await fetch(`${API_BASE}/generate-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    return res.json();
  },

  async getMember(memberId) {
    const res = await fetch(`${API_BASE}/member/${memberId}`);
    return res.json();
  },

  async getAllMembers() {
    const res = await fetch(`${API_BASE}/all-members`);
    return res.json();
  }
};