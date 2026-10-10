"use client";
export default function ErrorPage({ reset }: { reset: () => void }) { return <div className="state error" role="alert"><h1>เปิดหน้านี้ไม่ได้</h1><p>กรุณาลองใหม่ หากยังพบปัญหาให้ตรวจบริการข้อมูล</p><button onClick={reset}>ลองใหม่</button></div>; }
