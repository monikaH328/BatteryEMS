"""BatteryEMS web application: REST + Socket.IO around the shared controller."""
from __future__ import annotations
import threading,time,os
from flask import Flask,render_template,jsonify,Response,request
from flask_socketio import SocketIO,emit
import config,db
from backend.controller import BatteryController
from services.historical_service import HistoricalDataService
from services.alarm_service import AlarmService

app=Flask(__name__); app.config["SECRET_KEY"]="batteryems"
socketio=SocketIO(app,cors_allowed_origins="*",async_mode="threading")
db.init_database(); controller=BatteryController()
history_service=HistoricalDataService(); alarm_service=AlarmService()
_loop_started=False; _loop_lock=threading.Lock()

def history_payload(limit=None): return history_service.get_history(limit or config.MAX_HISTORY_POINTS)
def build_payload():
    live=controller.get_live_data()
    return {"schema_version":"1.0","timestamp":live["timestamp"],"bms":live["bms"],"ems":live["ems"],
            "hardware":live["hardware"],"simulation_running":live["simulation_running"],
            "alarms":alarm_service.evaluate(live["bms"]),"history":history_payload()}

def emit_update(): socketio.emit("update",build_payload())
def background_loop():
    while True:
        if not controller.paused: emit_update()
        time.sleep(config.TICK_INTERVAL_SECONDS)
def start_loop():
    global _loop_started
    with _loop_lock:
        if not _loop_started: socketio.start_background_task(background_loop); _loop_started=True

@app.route("/")
def index(): return render_template("index.html")
@app.route("/health")
def health(): return jsonify({"status":"ok","service":"BatteryEMS","schema_version":"1.0"})
@app.route("/api/live")
@app.route("/api/v1/live")
def api_live(): return jsonify(build_payload())
@app.route("/api/history")
@app.route("/api/v1/history")
def api_history(): return jsonify({"schema_version":"1.0","history":history_payload()})
@app.route("/api/statistics")
@app.route("/api/v1/statistics")
def api_statistics(): return jsonify({"schema_version":"1.0","statistics":history_service.statistics()})
@app.route("/api/faults")
@app.route("/api/v1/faults")
def api_faults(): return jsonify({"schema_version":"1.0","faults":history_service.faults()})
@app.route("/robots.txt")
def robots(): return Response("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",mimetype="text/plain")
@app.route("/sitemap.xml")
def sitemap():
    host=request.host_url.rstrip("/")
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+host+'/</loc></url></urlset>'
    return Response(xml,mimetype="application/xml")
@socketio.on("connect")
def on_connect(): emit("update",build_payload())
@socketio.on("command")
def handle_command(message):
    message=message or {}; command=message.get("type")
    actions={"grid_up":controller.grid_up,"grid_down":controller.grid_down,"clear":controller.clear_faults,
             "pause":controller.pause,"resume":controller.resume,"reset":controller.reset}
    if command=="fault": controller.inject_fault(message.get("fault","overvoltage"))
    elif command in actions: actions[command]()
    emit_update()
@socketio.on("request_update")
def request_update(): emit_update()
if __name__=="__main__":
    start_loop(); socketio.run(app,host=os.getenv("HOST","0.0.0.0"),port=int(os.getenv("PORT") or "5000"),debug=False,allow_unsafe_werkzeug=True)
