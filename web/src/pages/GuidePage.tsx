import {
  ArrowDown, ArrowRight, BookOpen, Clapperboard, FileVideo, History, ListChecks, PenLine, RefreshCw, Shirt, Sparkles,
  Wand2,
} from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type Step = {
  n: number
  icon: React.ComponentType<{ className?: string }>
  title: string
  what: string
  you: string[]
  claude: string[]
  out: string[]
  time: string
  freq: string
  link?: { to: string; label: string }
}

const STEPS: Step[] = [
  {
    n: 1, icon: FileVideo, title: 'Học video mẫu',
    what: 'Đưa vào một video dài (nhiều tập ghép liền) của bộ phim bạn muốn học cách kể. Máy bóc ra cốt truyện và tay nghề làm phim của nó.',
    you: ['Chọn file video trên máy', 'Chọn ngôn ngữ thoại (hoặc để tự nhận)'],
    claude: ['Dò điểm cắt cảnh, chia video thành đoạn ~2 phút', 'Chép lời thoại (chạy trên máy, không gửi đi đâu)',
      'Xem từng đoạn, ghi lại cảnh, nhân vật, thoại, góc máy, màu, âm thanh', 'Ghép thành một câu chuyện liền mạch',
      'Nhà phân tích phim soát lỗi và giải thích vì sao video cuốn người xem'],
    out: ['Cốt truyện, các hồi, các bí ẩn và lúc chúng được giải', 'Nhân vật chính / phụ: muốn gì, cần gì, giọng nói, ngoại hình',
      'Luật kể chuyện: nhịp cắt, góc máy, màu, âm thanh, cách móc câu cuối tập'],
    time: '20–60 phút (video 30 phút ≈ 40 phút)', freq: 'Hiếm: mỗi video mẫu một lần',
    link: { to: '/videos/new', label: 'Học video mẫu' },
  },
  {
    n: 2, icon: Wand2, title: 'Tạo phong cách viết',
    what: 'Biến những gì học được thành một "phong cách viết" dùng lại được. Phong cách giữ CÁCH kể (nhịp, cấu trúc, kiểu nhân vật), không giữ nội dung (tên, nơi chốn, sự kiện).',
    you: ['Bấm tạo phong cách ở trang video mẫu, đặt tên'],
    claude: ['Rút cốt truyện mẫu thành khung các nhịp truyện theo % độ dài season',
      'Viết khuôn vai nhân vật, luật kể chuyện, nhịp dựng, hình ảnh, âm thanh', 'Gắn yêu cầu cốt truyện bắt buộc (xem bên dưới)'],
    out: ['Một phong cách viết (ví dụ: "hollow-pine") dùng cho nhiều series'],
    time: '10–20 phút', freq: 'Hiếm: mỗi video mẫu một lần',
  },
  {
    n: 3, icon: BookOpen, title: 'Viết series: ý tưởng → bible → outline',
    what: 'Đưa ý tưởng của bạn, dù chỉ là vài dòng rời rạc. Claude kể nó theo phong cách đã chọn và dừng lại cho bạn đọc trước khi viết tập.',
    you: ['Dán ý tưởng: tóm tắt, vài cảnh, vài câu thoại, cái kết bạn muốn...', 'Chọn phong cách, số tập (10–20), độ dài mỗi tập (60–120 giây)'],
    claude: ['Ghép ý tưởng: ý nào của bạn ứng với nhịp truyện nào; chỗ trống thì sáng tác thêm',
      'Viết series bible: thế giới, luật, bối cảnh, nhân vật, bí ẩn và lời giải, cái kết',
      'Viết outline: từng tập làm gì, hé lộ gì, cao trào ở đâu, kết tập ra sao',
      'Tự kiểm tra cốt truyện, rồi tự biên tập chấm chiều sâu'],
    out: ['Ghép ý tưởng, Series bible, Outline', 'Kết quả kiểm tra cốt truyện và bản biên tập'],
    time: '10–25 phút', freq: 'Mỗi series một lần',
    link: { to: '/new', label: 'Series mới' },
  },
  {
    n: 4, icon: PenLine, title: 'Duyệt outline, viết tập, góp ý',
    what: 'Bạn đọc outline. Chưa ổn thì góp ý bằng lời; ổn thì duyệt để Claude viết từng tập. Sau đó đọc từng tập như đọc truyện, góp ý hoặc sửa trực tiếp, rồi chốt season.',
    you: ['Đọc outline, bản biên tập; góp ý hoặc bấm "Duyệt outline"', 'Đọc từng tập; bôi một đoạn để góp ý, hoặc "Sửa trực tiếp"',
      'Ở trang Biên tập: chọn các điểm cần sửa, bấm "Áp dụng"', 'Khi mọi tập ổn: "Chốt season"'],
    claude: ['Viết các tập song song: cảnh, thời gian, hành động, thoại, góc máy, ánh sáng, âm thanh',
      'Sửa theo góp ý: góp ý chung thì sửa vào phong cách (series sau cũng hưởng), góp ý riêng chỉ sửa series này',
      'Mỗi lần sửa là một phiên bản mới; bản cũ luôn được giữ để so sánh'],
    out: ['Kịch bản từng tập (đọc trên web, tải file .md)', 'Bản cuối trong final/ khi chốt season'],
    time: 'Viết 10 tập ≈ 20–30 phút; mỗi lần góp ý 3–10 phút', freq: 'Lặp đến khi bạn hài lòng',
  },
  {
    n: 5, icon: Shirt, title: 'Ngoại hình: nhân vật, trang phục, bối cảnh',
    what: 'Giữ mỗi nhân vật cùng một khuôn mặt, đúng trang phục, mỗi bối cảnh cùng một cách bày trí qua mọi tập. Có ảnh tham chiếu để làm video.',
    you: ['Mở nhóm "Ngoại hình": xem, sửa mô tả', 'Tạo ảnh tham chiếu, duyệt hoặc bỏ từng ảnh'],
    claude: ['Lập kho: mặt, tóc, dáng; trang phục theo từng tập; bối cảnh và biến thể ngày/đêm; đạo cụ',
      'Báo lỗi liên tục (ví dụ áo đổi màu giữa hai cảnh liền nhau)', 'Codex vẽ ảnh tham chiếu (bằng tài khoản ChatGPT của bạn)'],
    out: ['Kho nhân vật & bối cảnh', 'Ảnh tham chiếu đã duyệt'],
    time: 'Lập kho 5–15 phút; ảnh 1–4 phút mỗi ảnh (cả series ≈ 1 giờ)', freq: 'Sau outline, cập nhật sau khi viết tập',
  },
  {
    n: 6, icon: Clapperboard, title: 'Sản xuất video',
    what: 'Chia mỗi tập đã chốt thành các shot 1–5 giây, mỗi shot một prompt video tự đủ nghĩa, rồi tải gói đem sang Higgsfield.',
    you: ['Bấm "Tạo prompt video" (trang Tổng quan hoặc trang tập)', 'Bấm "Tải gói video" ở từng tập',
      'Với mỗi shot: upload ảnh tham chiếu, dán prompt, tải clip về', 'Ghép clip theo thứ tự, thêm phụ đề'],
    claude: ['Chia shot, viết prompt tiếng Anh cho model video (thoại giữ nguyên ngôn ngữ)', 'Gắn ảnh tham chiếu đã duyệt cho từng shot'],
    out: ['Gói zip mỗi tập: prompt từng shot, ảnh tham chiếu, phụ đề .srt, danh sách dựng .csv'],
    time: '3–8 phút mỗi tập', freq: 'Sau khi chốt season',
  },
]

const CONTRACT = [
  'Trọn vẹn từ mở đầu đến kết, kết có hậu hoặc kết buồn, xảy ra ngay trong tập cuối',
  'Có cốt truyện chính với một câu hỏi lớn',
  'Có nhân vật chính và các nhân vật phụ gắn với nhân vật chính',
  'Mỗi tập có lời thoại của ít nhất hai nhân vật',
  'Bối cảnh rõ ràng và thay đổi qua các tập',
  'Có cao trào giữa và cao trào cuối, không quá 3 tập liền không có cao trào',
  'Bí mật, bí ẩn có manh mối trước và lời giải sau',
]
const EDITOR = [
  'Chủ đề', 'Chiều sâu nhân vật chính', 'Nhân vật phụ', 'Phản diện / lực cản', 'Lời thoại và ẩn ý',
  'Gài và trả, cú lật công bằng', 'Mức cược và leo thang', 'Cảm xúc, cảnh có bước ngoặt', 'Độc đáo, tránh sáo mòn',
]

const TERMS: [string, string][] = [
  ['Video mẫu', 'Bộ phim bạn muốn học cách kể. Chỉ học cách kể, không chép nội dung.'],
  ['DNA', 'Mọi thứ học được từ video mẫu: cốt truyện, nhân vật, luật kể chuyện, kèm dẫn chứng (thời điểm, câu thoại).'],
  ['Phong cách viết', 'Bộ luật viết rút từ DNA. Một phong cách dùng được cho nhiều series khác nhau.'],
  ['Series bible', 'Sổ tay của series: thế giới, luật, bối cảnh, nhân vật, bí ẩn và lời giải, cái kết.'],
  ['Outline', 'Dàn ý cả season: mỗi tập một dòng, tập đó làm gì, hé lộ gì, kết ra sao.'],
  ['Phiên bản (v1, v2...)', 'Mỗi lần sửa tạo bản mới. Bản cũ không bao giờ bị ghi đè, luôn so sánh được.'],
  ['Chốt season', 'Lưu bản mới nhất của mọi tập thành bản cuối (final/), dùng cho sản xuất.'],
  ['Kho ngoại hình', 'Mô tả cố định của từng nhân vật, trang phục, bối cảnh, đạo cụ để mọi tập khớp nhau.'],
  ['Shot', 'Một cú máy 1–5 giây. Mỗi tập 60–120 giây có khoảng 25–50 shot.'],
  ['Canon', 'Những gì đã lên hình ở các tập đã quay. Khi viết tiếp, canon thắng kịch bản cũ.'],
]

const FAQ: [string, string][] = [
  ['Tôi có phải ngồi chờ không?', 'Không. Mọi việc chạy nền; bạn có thể đóng trang. Xong sẽ có thông báo, và mục "Việc" trên thanh trên cùng luôn cho biết việc nào đang chạy.'],
  ['Sao không bấm được nút khi đang có việc chạy?', 'Mỗi series chỉ chạy một việc một lúc để các bước không ghi đè lên nhau. Đợi việc đó xong rồi bấm tiếp.'],
  ['Ý tưởng của tôi khác video mẫu thì sao?', 'Ý tưởng của bạn luôn thắng. Phong cách chỉ quyết định cách kể; chỗ nào xung khắc, Claude chỉnh khung truyện theo ý bạn và ghi lại lý do.'],
  ['Góp ý chung và góp ý riêng khác nhau thế nào?', '"Cliffhanger lặp lại quá" là góp ý chung: sửa vào phong cách, series sau cũng tốt hơn. "Đổi tên Tuấn thành Minh" là góp ý riêng: chỉ sửa series này.'],
  ['Kiểm tra cốt truyện và Biên tập khác nhau thế nào?', 'Kiểm tra cốt truyện xem kịch bản có ĐỦ phần không (máy tự kiểm, vài giây). Biên tập xem các phần đó có HAY không (Claude đọc như biên tập viên, vài phút).'],
  ['Đã quay vài tập rồi muốn viết tiếp?', 'Bấm "Viết tiếp từ video đã quay" ở thanh bên của series (hoặc trang Viết tiếp series): đưa video đã quay vào, Claude đối chiếu với kịch bản (cái đã lên hình thắng) rồi viết outline phần tiếp.'],
  ['Dữ liệu có bị gửi đi đâu không?', 'Video, lời thoại và kịch bản nằm trên máy bạn (thư mục data/). Claude đọc qua Claude Code; ảnh tham chiếu vẽ qua Codex bằng tài khoản ChatGPT của bạn.'],
]

function List({ items, tone }: { items: string[]; tone?: 'muted' }) {
  return (
    <ul className={cn('space-y-1 text-sm', tone === 'muted' && 'text-muted-foreground')}>
      {items.map((x) => <li key={x} className="flex gap-2"><span className="mt-2 size-1 shrink-0 rounded-full bg-current opacity-60" />{x}</li>)}
    </ul>
  )
}

function StepCard({ s }: { s: Step }) {
  const Icon = s.icon
  return (
    <section id={`buoc-${s.n}`} className="scroll-mt-20 rounded-xl border bg-card p-5 sm:p-6">
      <div className="flex flex-wrap items-start gap-4">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">{s.n}</span>
        <div className="min-w-0 flex-1">
          <h3 className="flex items-center gap-2 text-lg font-semibold"><Icon className="size-5 opacity-70" />{s.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{s.what}</p>
        </div>
        {s.link && <Button render={<Link to={s.link.to} />} variant="outline" size="sm" className="gap-1">{s.link.label} <ArrowRight className="size-3.5" /></Button>}
      </div>
      <div className="mt-5 grid gap-5 md:grid-cols-3">
        <div>
          <div className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Bạn làm</div>
          <List items={s.you} />
        </div>
        <div>
          <div className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Claude làm</div>
          <List items={s.claude} tone="muted" />
        </div>
        <div>
          <div className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Kết quả</div>
          <List items={s.out} />
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-x-6 gap-y-1 border-t pt-3 text-xs text-muted-foreground">
        <span>Thời gian: <span className="text-foreground">{s.time}</span></span>
        <span>Tần suất: <span className="text-foreground">{s.freq}</span></span>
      </div>
    </section>
  )
}

export function GuidePage() {
  return (
    <main className="mx-auto max-w-5xl space-y-10 px-4 py-8 sm:py-10">
      <header>
        <div className="flex items-center gap-2 text-sm font-medium text-primary"><Sparkles className="size-4" /> Hướng dẫn</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">story-dna làm gì?</h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-muted-foreground">
          Học cách kể chuyện từ một bộ phim bạn thích, rồi dùng đúng cách kể đó để biến ý tưởng của bạn thành một series phim ngắn dọc
          10–20 tập (mỗi tập 1–2 phút): có cốt truyện trọn vẹn, nhân vật, thoại, bối cảnh, và sẵn sàng đem đi làm video.
        </p>
      </header>

      {/* Overview: the 6 steps at a glance */}
      <section>
        <h2 className="text-lg font-semibold">Toàn bộ quy trình</h2>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
          {STEPS.map((s, i) => {
            const Icon = s.icon
            return (
              <li key={s.n} className="relative">
                <a href={`#buoc-${s.n}`} className="flex h-full flex-col gap-2 rounded-lg border bg-card p-3 text-sm transition hover:border-primary/40 hover:shadow-sm">
                  <span className="flex items-center gap-2">
                    <span className="flex size-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">{s.n}</span>
                    <Icon className="size-4 opacity-70" />
                  </span>
                  <span className="font-medium leading-snug">{s.title}</span>
                  <span className="text-xs text-muted-foreground">{s.freq}</span>
                </a>
                {i < STEPS.length - 1 && (
                  <ArrowRight className="absolute top-1/2 -right-2.5 z-10 hidden size-4 -translate-y-1/2 rounded-full bg-background text-muted-foreground lg:block" />
                )}
              </li>
            )
          })}
        </ol>
        <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div className="rounded-lg bg-muted/50 p-3"><span className="font-medium">Bước 1–2:</span> làm một lần cho mỗi video mẫu.</div>
          <div className="rounded-lg bg-muted/50 p-3"><span className="font-medium">Bước 3–4:</span> mỗi series, lặp góp ý đến khi hài lòng.</div>
          <div className="rounded-lg bg-muted/50 p-3"><span className="font-medium">Bước 5–6:</span> chuẩn bị và làm video.</div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Từng bước</h2>
        {STEPS.map((s, i) => (
          <div key={s.n}>
            <StepCard s={s} />
            {i < STEPS.length - 1 && <ArrowDown className="mx-auto mt-4 size-5 text-muted-foreground" />}
          </div>
        ))}
        <div className="flex flex-wrap items-start gap-4 rounded-xl border border-dashed p-5">
          <RefreshCw className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
          <div className="text-sm">
            <div className="font-medium">Viết tiếp sau khi đã quay</div>
            <p className="mt-1 text-muted-foreground">
              Đã làm vài tập thành video? Đưa các video đó vào, Claude đối chiếu với kịch bản (cái đã lên hình được giữ), cập nhật bible,
              rồi viết outline cho các tập tiếp theo: theo hướng cũ hoặc mở một mạch truyện mới. Làm được cả với series không viết ở đây.
            </p>
            <Link to="/continue" className="mt-2 inline-flex items-center gap-1 text-primary hover:underline">Viết tiếp series <ArrowRight className="size-3.5" /></Link>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Hai lớp kiểm tra chất lượng kịch bản</h2>
        <p className="mt-1 text-sm text-muted-foreground">Chạy tự động sau khi có outline. Kết quả nằm ở trang Tổng quan và trang Biên tập của series.</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border bg-card p-5">
            <h3 className="flex items-center gap-2 font-semibold"><ListChecks className="size-4" /> Kiểm tra cốt truyện: có đủ chưa?</h3>
            <p className="mt-1 text-xs text-muted-foreground">Máy tự kiểm trong vài giây. Thiếu gì, Claude bổ sung (bấm "Sửa tự động").</p>
            <ol className="mt-3 space-y-1.5 text-sm">
              {CONTRACT.map((c, i) => <li key={c} className="flex gap-2"><span className="w-4 shrink-0 text-right text-muted-foreground tabular-nums">{i + 1}.</span>{c}</li>)}
            </ol>
          </div>
          <div className="rounded-xl border bg-card p-5">
            <h3 className="flex items-center gap-2 font-semibold"><PenLine className="size-4" /> Biên tập: có hay không?</h3>
            <p className="mt-1 text-xs text-muted-foreground">Claude đọc như biên tập viên, chấm 1–5 mỗi tiêu chí kèm dẫn chứng, đề xuất cách sửa; bạn chọn điểm nào thì sửa điểm đó.</p>
            <ol className="mt-3 grid gap-x-4 gap-y-1.5 text-sm sm:grid-cols-2">
              {EDITOR.map((c, i) => <li key={c} className="flex gap-2"><span className="w-4 shrink-0 text-right text-muted-foreground tabular-nums">{i + 1}.</span>{c}</li>)}
            </ol>
            <p className="mt-3 text-xs text-muted-foreground">Đạt khi mọi tiêu chí từ 3 trở lên và trung bình từ 3.5.</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Thuật ngữ</h2>
        <dl className="mt-4 grid gap-x-6 gap-y-3 rounded-xl border bg-card p-5 text-sm sm:grid-cols-2">
          {TERMS.map(([t, d]) => (
            <div key={t}>
              <dt className="font-medium">{t}</dt>
              <dd className="text-muted-foreground">{d}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2 className="flex items-center gap-2 text-lg font-semibold"><History className="size-4" /> Câu hỏi thường gặp</h2>
        <div className="mt-4 divide-y rounded-xl border bg-card">
          {FAQ.map(([q, a]) => (
            <details key={q} className="group px-5 py-3">
              <summary className="cursor-pointer list-none text-sm font-medium marker:hidden">
                <span className="mr-2 inline-block text-muted-foreground transition group-open:rotate-90">›</span>{q}
              </summary>
              <p className="mt-2 pl-4 text-sm text-muted-foreground">{a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-primary/5 p-6">
        <div>
          <div className="font-semibold">Bắt đầu từ đâu?</div>
          <p className="mt-1 text-sm text-muted-foreground">Chưa có phong cách viết nào: học một video mẫu trước. Đã có: tạo series mới ngay.</p>
        </div>
        <div className="flex gap-2">
          <Button render={<Link to="/videos/new" />} variant="outline">Học video mẫu</Button>
          <Button render={<Link to="/new" />}>Series mới</Button>
        </div>
      </section>
    </main>
  )
}
