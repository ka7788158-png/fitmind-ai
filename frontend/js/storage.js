const DB = {
  getMember: () => JSON.parse(localStorage.getItem('fm_member') || 'null'),
  setMember: (data) => localStorage.setItem('fm_member', JSON.stringify(data)),
  clearMember: () => {
    const member = DB.getMember();
    localStorage.setItem('fm_member', 'null');
  },

  // get current member id prefix
  _id: () => {
    const m = JSON.parse(localStorage.getItem('fm_member') || 'null');
    return m ? m.id || m.member_id || 'guest' : 'guest';
  },

  getDailyLog: (date) => JSON.parse(localStorage.getItem(`fm_${DB._id()}_log_${date}`) || 'null'),
  setDailyLog: (date, data) => localStorage.setItem(`fm_${DB._id()}_log_${date}`, JSON.stringify(data)),

  getStreak: () => parseInt(localStorage.getItem(`fm_${DB._id()}_streak`) || '0'),
  setStreak: (n) => localStorage.setItem(`fm_${DB._id()}_streak`, n),

  getLastActive: () => localStorage.getItem(`fm_${DB._id()}_last_active`),
  setLastActive: (date) => localStorage.setItem(`fm_${DB._id()}_last_active`, date),

  getProgress: () => JSON.parse(localStorage.getItem(`fm_${DB._id()}_progress`) || '[]'),
  addProgress: (entry) => {
    const data = DB.getProgress();
    data.push(entry);
    localStorage.setItem(`fm_${DB._id()}_progress`, JSON.stringify(data));
  },

  getWater: (date) => parseInt(localStorage.getItem(`fm_${DB._id()}_water_${date}`) || '0'),
  setWater: (date, ml) => localStorage.setItem(`fm_${DB._id()}_water_${date}`, ml),

  getHeatmap: () => JSON.parse(localStorage.getItem(`fm_${DB._id()}_heatmap`) || '{}'),
  markDay: (date, level) => {
    const hm = DB.getHeatmap();
    hm[date] = level;
    localStorage.setItem(`fm_${DB._id()}_heatmap`, JSON.stringify(hm));
  },

  getCalories: (date) => JSON.parse(localStorage.getItem(`fm_${DB._id()}_cal_${date}`) || '{}'),
  setCalories: (date, data) => localStorage.setItem(`fm_${DB._id()}_cal_${date}`, JSON.stringify(data)),

  today: () => new Date().toISOString().split('T')[0]
};